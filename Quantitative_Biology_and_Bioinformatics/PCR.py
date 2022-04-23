'''This program uses my reverse complement function to identify predicted PCR products
for sets of primer pairs in pBR322_PCR_primers.txt used in virtual PCR on the DNA sequence of'''

# (1) Define the reverse_complement function:


def reverse_complement(dna):
    '''Function to return the reverse complement of a DNA string'''
    # initialize empty string to collect the complemented bases
    complement_bases = []
    # iterate over each base in the input DNA sequence and append the
    # corresponding complementary base (using an if/elif/else
    # statement)
    for base in dna:
        if base == 'A':
            complement_bases.append('T')
        elif base == 'T':
            complement_bases.append('A')
        elif base == 'C':
            complement_bases.append('G')
        elif base == 'G':
            complement_bases.append('C')
        else:
            print('Illegal base: %s' % base)

    # use the list reverse method to reverse the bases
    complement_bases.reverse()

    # join the individual bases into a string
    reverse_complement_dna = ''.join(complement_bases)

    return reverse_complement_dna


# (2) Load the pBR322 sequence:
with open('pBR322.txt', 'r') as file:
    content = file.read()


# (3) Assemble the pBR322 sequence into a contiguous string:
# split on intervening spaces (newlines) to generate a list of
# lines and then join into one string
lines = content.strip().split()
pBR322 = ''.join(lines)

# (4) Load the pairs of PCR primers.
fh_in = open('pBR322_PCR_primers.txt', 'r')

# (5) Open an output file:
fh_out = open('pBR322_PCR_products.txt', 'w')

# (6) Iterate over each primer pair and identify its corresponding PCR product:
for line in fh_in:
    primer_pair = line.strip().split(',')
    fwd_primer = primer_pair[0]
    # generate the reverse complement of the reverse primer so that
    # it will match the pBR322 forward-strand sequence
    ## rev_primer = DNATools.reverse_complement(primer_pair[1])
    rev_primer = reverse_complement(primer_pair[1])

    # find the start positions of each primer
    fwd_start = pBR322.find(fwd_primer)
    rev_start = pBR322.find(rev_primer)

    # compute the end position of the rev_primer by adding its length
    # to its start position
    rev_end = rev_start + len(rev_primer)

    # slice out the PCR product
    pcr_product = pBR322[fwd_start: rev_end]

    # write the primer sequences as well as the corresponding PCR
    # product
    fh_out.write(fwd_primer + ', ' + rev_primer + ', ' + pcr_product + ', ' + str(len(pcr_product)) + '\n\n')

fh_out.close()
fh_in.close()
