

def replace_infile(pathin, pathout, replacements):
    """
    it replaces all the occurences of a word for another one included in a dictionary
    :param pathin: the path for the input file
    :param pathout: the path where the output file will be copied
    :param replacements: a dictionary with the replacements we want to make e.g. replacements={"@namenode@":"paravance-5.grid5000.fr"}
    """
    with open(pathin) as infile, open(pathout, 'w') as outfile:
        for line in infile:
            for src, target in replacements.iteritems():
                line = line.replace(src, target)
            outfile.write(line)

