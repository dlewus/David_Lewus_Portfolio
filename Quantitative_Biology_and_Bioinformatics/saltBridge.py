'''This program determines the salt bridge locations on the hemoglobin protein'''

import math


def dist(x1, y1, z1, x2, y2, z2):
    '''This function computes the standard distance formula.'''
    return math.sqrt(((x1 - x2)**2) + ((y1 - y2)**2) + ((z1 - z2)**2))


for i in [1, 2]:   # run the code two times
    if i == 1:
        in_filename = '1hho_tetramer.pdb'  # filename for the oxyhemoglobin tetramer
    else:
        in_filename = '2hhb.pdb'        # filename for the deoxyhemoglobin tetramer
    print(in_filename)
    fh_in = open(in_filename, 'r')  # input file

    chain = []  # empty list

    for line in fh_in:  # iterates through each line in input file
        sline = line.split()  # splits each line, and appends a list of relevant items from each line
        if sline[0] == 'ATOM':
            if sline[3] == 'ARG' and sline[2] == 'CZ':
                coord = [sline[3], sline[5], sline[4], sline[6], sline[7], sline[8], 1]
                chain.append(coord)
            elif sline[3] == 'ASP' and sline[2] == 'CG':
                coord = [sline[3], sline[5], sline[4], sline[6], sline[7], sline[8], -1]
                chain.append(coord)
            elif sline[3] == 'LYS' and sline[2] == 'NZ':
                coord = [sline[3], sline[5], sline[4], sline[6], sline[7], sline[8], 1]
                chain.append(coord)
            elif sline[3] == 'GLU' and sline[2] == 'CD':
                coord = [sline[3], sline[5], sline[4], sline[6], sline[7], sline[8], -1]
                chain.append(coord)

    fh_in.close()  # input file closed

    if i == 1:
        fh_out = open('oxy.txt', 'w')  # opens intra output file as appendable
    else:
        fh_out = open('deoxy.txt', 'w')  # opens intra output file as appendable

    fh_out.write("1st residue       2nd residue       distance        energy       comparison type\n")

    intra = []  # empty list
    inter = []  # empty list

    for i, first in enumerate(chain):  # iterates over the list of data from the PDB file
        for j, second in enumerate(chain):  # iterates over the list of data from the PDB file
            if j > i:  # excludes duplicate comparisons
                x1 = float(first[3])
                x2 = float(second[3])
                y1 = float(first[4])
                y2 = float(second[4])
                z1 = float(first[5])
                z2 = float(second[5])
                distance = dist(x1, y1, z1, x2, y2, z2)

                if distance < 8:
                    dist_list = [distance, first[0], second[0], first[6], second[6], first[1], second[1], first[2], second[2]]
                    energy = 332.0 * (float((dist_list[3] * dist_list[4]) / (40.0 * dist_list[0])))  # calculate the bond energy

                    outline1 = "\t".join([str(dist_list[1]), str(dist_list[5]), str(dist_list[7]), str(dist_list[2]), str(dist_list[6]), str(dist_list[8])])
                    outline2 = "\t" + "{:.2f}".format(dist_list[0]) + "\t" + "{:.2f}".format(energy)
                    if first[2] != second[2]:
                        outline3 = "\tINTER\n"
                    else:
                        outline3 = "\tINTRA\n"

                    fh_out.write(outline1 + outline2 + outline3)

fh_out.close()  # closes output file
