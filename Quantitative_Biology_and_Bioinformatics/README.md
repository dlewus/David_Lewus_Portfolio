# Quantitative Biology and Bioinformatics
These programs were developed for the course I help instruct at Rutgers, [Quantitative Biology and Bioinformatics](https://biology.rutgers.edu/29-spring-courses/genetics-2/184-447-302-quantitative-biology-bioinformatics).

### DNAtoAA.py
This file translates a DNA string into an amino acid string. For a valid amino acid string to be produced, the DNA string must begin with a start codon and end with a stop codon

### PCR.py
This file uses the given PCR primers to find the associated PCR products and their lengths within the plasmid pBR322. Theoretically this code could be adapted for any PCR primers and target sequence by changing the input files.

### findORF.py
This file finds all open reading frames for any provided DNA sequence. An open reading frame (ORF) is one which starts from the start codon and ends by stop codon, without any other stop codons in between. Thus, a candidate protein string is derived by translating an open reading frame into amino acids until a stop codon is reached.

### saltBridge.py
This file determines the locations of all salt bridges on the folded hemoglobin protein. Theoretically this code could be adapted for any protein by changing the input .pdb files.
