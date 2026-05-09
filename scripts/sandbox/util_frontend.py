#!/usr/bin/env python
"""
util_frontend.py

Utilities for frontend feature extraction

It includes:
 LFCC: based on asvspoof.org baseline matlab code
 LFB: Linear filterbank feature
      Chen, T., Kumar, A., Nagarsheth, P., Sivaraman, G. & Khoury, E. 
      Generalization of Audio Deepfake Detection. in Proc. Odyssey 132-137 
      (2020). doi:10.21437/Odyssey.2020-19 

      According to the author's email:
      LFB = np.log(FilterBank(Amplitude(STFT(x))))
      There is no DCT. But it does have logarithm.

      Implemented based on LFCC API
 
"""

from __future__ import absolute_import
from __future__ import print_function

import sys
import numpy as np
from spafe.features.cqcc import cqcc

import torch
import torch.nn as torch_nn
import torch.nn.functional as torch_nn_func
import sandbox.util_dsp as nii_dsp
import core_scripts.data_io.conf as nii_conf

__author__ = "Xin Wang"
__email__ = "wangxin@nii.ac.jp"
__copyright__ = "Copyright 2021, Xin Wang"

##################
## other utilities
##################
def trimf(x, params):
    """
    trimf: similar to Matlab definition
    https://www.mathworks.com/help/fuzzy/trimf.html?s_tid=srchtitle
    
    """
    if len(params) != 3:
        print("trimp requires params to be a list of 3 elements")
        sys.exit(1)
    a = params[0]
    b = params[1]
    c = params[2]
    if a > b or b > c:
        print("trimp(x, [a, b, c]) requires a<=b<=c")
        sys.exit(1)
    y = torch.zeros_like(x, dtype=nii_conf.d_dtype)
    if a < b:
        index = torch.logical_and(a < x, x < b)
        y[index] = (x[index] - a) / (b - a)
    if b < c:    
        index = torch.logical_and(b < x, x < c)              
        y[index] = (c - x[index]) / (c - b)
    y[x == b] = 1
    return y 
    
def delta(x):
    """ By default
    input
    -----
    x (batch, Length, dim)
    
    output
    ------
    output (batch, Length, dim)
    
    Delta is calculated along Length dimension
    """
    length = x.shape[1]
    output = torch.zeros_like(x)
    x_temp = torch_nn_func.pad(x.unsqueeze(1), (0, 0, 1, 1), 
                               'replicate').squeeze(1)
    output = -1 * x_temp[:, 0:length] + x_temp[:,2:]
    return output


def linear_fb(fn, sr, filter_num):
    """linear_fb(fn, sr, filter_num)
    create linear filter bank based on trim

    input
    -----
      fn: int, FFT points
      sr: int, sampling rate (Hz)
      filter_num: int, number of filters in filter-bank
    
    output
    ------
      fb: tensor, (fn//2+1, filter_num)

    Note that this filter bank is supposed to be used on 
    spectrum of dimension fn//2+1.

    See example in LFCC.
    """
    # build the triangle filter bank
    f = (sr / 2) * torch.linspace(0, 1, fn//2+1)
    filter_bands = torch.linspace(min(f), max(f), filter_num+2)
        
    filter_bank = torch.zeros([fn//2+1, filter_num])
    for idx in range(filter_num):
        filter_bank[:, idx] = trimf(
            f, [filter_bands[idx], 
                filter_bands[idx+1], 
                filter_bands[idx+2]])
    return filter_bank

#################
## LFCC front-end
#################

class LFCC(torch_nn.Module):
    """ Based on asvspoof.org baseline Matlab code.
    Difference: with_energy is added to set the first dimension as energy
    """
    def __init__(self, fl, fs, fn, sr, filter_num, 
                 with_energy=False, with_emphasis=True,
                 with_delta=True, flag_for_LFB=False,
                 num_coef=None, min_freq=0, max_freq=1):
        """ Initialize LFCC
        
        Para:
        -----
          fl: int, frame length, (number of waveform points)
          fs: int, frame shift, (number of waveform points)
          fn: int, FFT points
          sr: int, sampling rate (Hz)
          filter_num: int, number of filters in filter-bank

          with_energy: bool, (default False), whether replace 1st dim to energy
          with_emphasis: bool, (default True), whether pre-emphaze input wav
          with_delta: bool, (default True), whether use delta and delta-delta
        
          for_LFB: bool (default False), reserved for LFB feature
          num_coef: int or None, number of coeffs to be taken from filter bank.
                    Note that this is only used for LFCC, i.e., for_LFB=False
                    When None, num_coef will be equal to filter_num
          min_freq: float (default 0), min_freq * sr // 2 will be the minimum 
                    frequency of extracted FFT spectrum
          max_freq: float (default 1), max_freq * sr // 2 will be the maximum 
                    frequency of extracted FFT spectrum
        """
        super(LFCC, self).__init__()
        self.fl = fl
        self.fs = fs
        self.fn = fn
        self.sr = sr
        self.filter_num = filter_num
        self.num_coef = num_coef

        # decide the range of frequency bins
        if min_freq >= 0 and min_freq < max_freq and max_freq <= 1:
            self.min_freq_bin = int(min_freq * (fn//2+1))
            self.max_freq_bin = int(max_freq * (fn//2+1))
            self.num_fft_bins = self.max_freq_bin - self.min_freq_bin 
        else:
            print("LFCC cannot work with min_freq {:f} and max_freq {:}".format(
                min_freq, max_freq))
            sys.exit(1)
        
        # build the triangle filter bank
        f = (sr / 2) * torch.linspace(min_freq, max_freq, self.num_fft_bins)
        filter_bands = torch.linspace(min(f), max(f), filter_num+2)
        
        filter_bank = torch.zeros([self.num_fft_bins, filter_num])
        for idx in range(filter_num):
            filter_bank[:, idx] = trimf(
                f, [filter_bands[idx], 
                    filter_bands[idx+1], 
                    filter_bands[idx+2]])
        self.lfcc_fb = torch_nn.Parameter(filter_bank, requires_grad=False)

        # DCT as a linear transformation layer
        self.l_dct = nii_dsp.LinearDCT(filter_num, 'dct', norm='ortho')

        # opts
        self.with_energy = with_energy
        self.with_emphasis = with_emphasis
        self.with_delta = with_delta
        self.flag_for_LFB = flag_for_LFB
        if self.num_coef is None:
            self.num_coef = filter_num
        
        return
    
    def forward(self, x):
        """
        
        input:
        ------
         x: tensor(batch, length), where length is waveform length
        
        output:
        -------
         lfcc_output: tensor(batch, frame_num, dim_num)
        """
        # pre-emphsis 
        if self.with_emphasis:
            # to avoid side effect
            x_copy = torch.zeros_like(x) + x
            x_copy[:, 1:] = x[:, 1:]  - 0.97 * x[:, 0:-1]
        else:
            x_copy = x
        
        # STFT
        x_stft = torch.view_as_real(torch.stft(x_copy, self.fn, self.fs, self.fl, 
                            window=torch.hamming_window(self.fl).to(x.device), 
                            onesided=True, pad_mode="constant", return_complex=True))        
        # amplitude
        sp_amp = torch.norm(x_stft, 2, -1).pow(2).permute(0, 2, 1).contiguous()
        
        if self.min_freq_bin > 0 or self.max_freq_bin < (self.fn//2+1):
            sp_amp = sp_amp[:, :, self.min_freq_bin:self.max_freq_bin]
        
        # filter bank
        fb_feature = torch.log10(torch.matmul(sp_amp, self.lfcc_fb) + 
                                 torch.finfo(torch.float32).eps)
        
        # DCT (if necessary, remove DCT)
        lfcc = self.l_dct(fb_feature) if not self.flag_for_LFB else fb_feature
        
        # Truncate the output of l_dct when necessary
        if not self.flag_for_LFB and self.num_coef != self.filter_num:
            lfcc = lfcc[:, :, :self.num_coef]
            

        # Add energy 
        if self.with_energy:
            power_spec = sp_amp / self.fn
            energy = torch.log10(power_spec.sum(axis=2)+ 
                                 torch.finfo(torch.float32).eps)
            lfcc[:, :, 0] = energy

        # Add delta coefficients
        if self.with_delta:
            lfcc_delta = delta(lfcc)
            lfcc_delta_delta = delta(lfcc_delta)
            lfcc_output = torch.cat((lfcc, lfcc_delta, lfcc_delta_delta), 2)
        else:
            lfcc_output = lfcc

        # done
        return lfcc_output

#################
## LFB front-end
#################

class LFB(LFCC):
    """ Linear filterbank feature
      Chen, T., Kumar, A., Nagarsheth, P., Sivaraman, G. & Khoury, E. 
      Generalization of Audio Deepfake Detection. in Proc. Odyssey 132-137 
      (2020). doi:10.21437/Odyssey.2020-19 
       
    """
    def __init__(self, fl, fs, fn, sr, filter_num, 
                 with_energy=False, with_emphasis=True,
                 with_delta=False):
        """ Initialize LFB
        
        Para:
        -----
          fl: int, frame length, (number of waveform points)
          fs: int, frame shift, (number of waveform points)
          fn: int, FFT points
          sr: int, sampling rate (Hz)
          filter_num: int, number of filters in filter-bank
          with_energy: bool, (default False), whether replace 1st dim to energy
          with_emphasis: bool, (default True), whether pre-emphaze input wav
          with_delta: bool, (default True), whether use delta and delta-delta
        """
        super(LFB, self).__init__(fl, fs, fn, sr, filter_num, with_energy,
                                  with_emphasis, with_delta, flag_for_LFB=True)
        return
    
    def forward(self, x):
        """
        input:
        ------
         x: tensor(batch, length), where length is waveform length
        
        output:
        -------
         lfb_output: tensor(batch, frame_num, dim_num)
        """
        return super(LFB, self).forward(x)


#################
## Spectrogram (FFT) front-end
#################

class Spectrogram(torch_nn.Module):
    """ Spectrogram front-end
    """
    def __init__(self, fl, fs, fn, sr, 
                 with_emphasis=True, with_delta=False):
        """ Initialize LFCC
        
        Para:
        -----
          fl: int, frame length, (number of waveform points)
          fs: int, frame shift, (number of waveform points)
          fn: int, FFT points
          sr: int, sampling rate (Hz)
          with_emphasis: bool, (default True), whether pre-emphaze input wav
          with_delta: bool, (default False), whether use delta and delta-delta
        
        """
        super(Spectrogram, self).__init__()
        self.fl = fl
        self.fs = fs
        self.fn = fn
        self.sr = sr
        
        # opts
        self.with_emphasis = with_emphasis
        self.with_delta = with_delta
        return
    
    def forward(self, x):
        """
        
        input:
        ------
         x: tensor(batch, length), where length is waveform length
        
        output:
        -------
         lfcc_output: tensor(batch, frame_num, dim_num)
        """
        # pre-emphsis 
        if self.with_emphasis:
            x[:, 1:] = x[:, 1:]  - 0.97 * x[:, 0:-1]
        
        # STFT
        x_stft = torch.view_as_real(torch.stft(x, self.fn, self.fs, self.fl, 
                            window=torch.hamming_window(self.fl).to(x.device), 
                            onesided=True, pad_mode="constant"))        
        # amplitude
        sp_amp = torch.norm(x_stft, 2, -1).pow(2).permute(0, 2, 1).contiguous()
        
        # Add delta coefficients
        if self.with_delta:
            sp_delta = delta(sp_amp)
            sp_delta_delta = delta(sp_delta)
            sp_output = torch.cat((sp_amp, sp_delta, sp_delta_delta), 2)
        else:
            sp_output = sp_amp

        # done
        return sp_amp

import torchaudio.transforms as T

#################
## E5 Universal Feature Extractor
#################
class UniversalFeatureExtractor(torch_nn.Module):
    def __init__(self, feature_type='mfcc', fl=320, fs=160, fn=512, sr=16000, filter_num=20):
        super(UniversalFeatureExtractor, self).__init__()
        self.feature_type = feature_type.lower()
        self.sr = sr
        
        # 1. Setup LFCC
        self.lfcc_extractor = LFCC(fl=fl, fs=fs, fn=fn, sr=sr, filter_num=filter_num, 
                                   with_energy=True, with_emphasis=True, with_delta=True)
        
        # 2. Setup MFCC
        self.mfcc_extractor = T.MFCC(sample_rate=sr, n_mfcc=filter_num, melkwargs={"n_mels": filter_num})
        self.delta_extractor = T.ComputeDeltas()

    def _get_mfcc(self, x):
        """Helper to extract 60-dim MFCC (20 static + 20 delta + 20 delta-delta)"""
        mfcc_static = self.mfcc_extractor(x)
        mfcc_delta = self.delta_extractor(mfcc_static)
        mfcc_delta2 = self.delta_extractor(mfcc_delta)
        mfcc_stacked = torch.cat((mfcc_static, mfcc_delta, mfcc_delta2), dim=1)
        return mfcc_stacked.permute(0, 2, 1) # Shape: (batch, frames, 60)

    def _get_cqcc(self, x):
        """Helper to extract 60-dim CQCC using spafe"""
        batch_size = x.shape[0]
        cqcc_batch = []
        for i in range(batch_size):
            wav_np = x[i].detach().cpu().numpy()
            feat = cqcc(wav_np, fs=self.sr, num_ceps=60)
            feat_tensor = torch.from_numpy(feat).float().to(x.device)
            cqcc_batch.append(feat_tensor)
        return torch.stack(cqcc_batch) # Shape: (batch, frames, 60)

    def forward(self, x):
        """
        x shape: (batch_size, waveform_length)
        """
        if self.feature_type == 'lfcc':
            return self.lfcc_extractor(x)
            
        elif self.feature_type == 'mfcc':
            return self._get_mfcc(x)
            
        elif self.feature_type == 'cqcc':
            return self._get_cqcc(x)
            
        elif self.feature_type == 'fusion':
            # 1. Extract ALL THREE (60 dims each)
            lfcc_out = self.lfcc_extractor(x)
            mfcc_out = self._get_mfcc(x)
            cqcc_out = self._get_cqcc(x)
            
            # 2. Make sure frame lengths match exactly before concatenating
            # (Different extractors might have 1-2 frames difference due to padding)
            min_frames = min(lfcc_out.shape[1], mfcc_out.shape[1], cqcc_out.shape[1])
            lfcc_out = lfcc_out[:, :min_frames, :]
            mfcc_out = mfcc_out[:, :min_frames, :]
            cqcc_out = cqcc_out[:, :min_frames, :]
            
            # 3. Concatenate along the feature dimension (dim=2)
            # 60 + 60 + 60 = 180 Dimensions!
            fusion_out = torch.cat((lfcc_out, mfcc_out, cqcc_out), dim=2)
            
            return fusion_out
            
        else:
            print(f"Feature type {self.feature_type} not supported yet!")
            sys.exit(1)

if __name__ == "__main__":
    print("Definition of front-end for Anti-spoofing")
