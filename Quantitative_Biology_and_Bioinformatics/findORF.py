'''This program finds all open reading frames for any provided DNA sequence'''

dna = 'AGCCATGTAGCTAACTCAGGTTACATGGGGATGACCCCGCGACTTGGATTAGAGTCTCTTTTGGAATAAGCCTGAATGATCCGAGTAGCATCTCAG'

# set up codon dictionary
with open('codons.txt', 'r') as codon:
    codon_dict = {}

    for line in codon:
        line = line.strip().split('\t')
        codon_dict[line[0]] = line[1]

# find reverse complement of DNA string
forward = dna
reverse = ''
for base in dna:
    if base == 'A':
        reverse += 'T'
    elif base == 'T':
        reverse += 'A'
    elif base == 'G':
        reverse += 'C'
    elif base == 'C':
        reverse += 'G'
reverse = reverse[::-1]


output = []

# look at positions in DNA for codons, don't need to look at last 2 because they won't form a full codon
for i in range(len(forward) - 2):
    # find a start codon
    if forward[i:i + 3] == 'ATG':
        seq = ''
        # translate the entirety of the DNA after the start codon to aa
        for pos in range(i, len(forward), 3):
            if len(forward) - pos >= 3:
                codon = forward[pos:pos + 3]
                seq += codon_dict[codon]
        # search through aa string to find stop codon
        for j in range(len(seq)):
            if seq[j] == '*':
                if seq[:j + 1] not in output:
                    # only append aa string up to and including stop codon
                    # don't append duplicates
                    output.append(seq[:j + 1])
                break

# repeat for reverse complement
for i in range(len(reverse) - 2):
    if reverse[i:i + 3] == 'ATG':
        seq = ''
        for pos in range(i, len(reverse), 3):
            if len(reverse) - pos >= 3:
                codon = reverse[pos:pos + 3]
                seq += codon_dict[codon]
        for j in range(len(seq)):
            if seq[j] == '*':
                if seq[:j + 1] not in output:
                    output.append(seq[:j + 1])
                break

for seq in output:
    print(seq)
