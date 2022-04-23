# Open needed files and creates, variables to be used later
codon = open('codons.txt', 'r')
spe_in = open('spe-9.txt', 'r')
spe_out = open('SPE_Protein.txt', 'w')
codon_dict = {}
spe_9 = []

# Put the codons into a dictionary
for line in codon:
    line = line.strip().split('\t')
    codon_dict[line[0]] = line[1]

# Read in the sequence of spe-9 and apends it to a list as groupings of 3 letters
gene = spe_in.read()
for num in range(0, len(gene), 3):
    spe_9.append(gene[num:num + 3])

# Translate the list and write it to the output
for triplet in spe_9:
    spe_out.write(codon_dict[triplet])


# Close used files
codon.close()
spe_in.close()
spe_out.close()
