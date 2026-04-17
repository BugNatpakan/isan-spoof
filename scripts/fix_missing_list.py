"""
    fix the missing files in dev.lst by extracting the official file names from the original protocol file (ASVspoof2019.LA.cm.dev.trl.txt)
    and save the new dev.lst to the scp directory
"""


dev_lst_path = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\asvspoof2019\scp\dev.lst"
dev_protocal_path = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\asvspoof2019\ASVspoof2019.LA.cm.dev.trl.txt"

eval_lst_path = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\asvspoof2019\scp\eval.lst"
eval_protocal_path = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\asvspoof2019\ASVspoof2019.LA.cm.eval.trl.txt"

# Point this to your original, untouched dev answer key
protocol_file = eval_lst_path
output_list = eval_protocal_path

# Open the answer key and extract ONLY the official filenames
with open(protocol_file, 'r') as f:
    lines = f.readlines()

valid_files = []
for line in lines:
    parts = line.strip().split()
    if len(parts) >= 2:
        # Grab the second column (the LA_D_XXXXXXX file name)
        valid_files.append(parts[1]) 

# Save those valid names to your dev.lst
with open(output_list, 'w') as f:
    for file in valid_files:
        f.write(file + "\n")

print(f"Success! Created a new {output_list} with exactly {len(valid_files)} matching files.")