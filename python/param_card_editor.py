import os
import pandas as pd

class BlockEntry:
    def __init__(self, v, comment):
        self.v = float(v)
        self.comment = comment.strip()
    def __repr__(self):
        return str(self.v) + " #" + self.comment

class ParamCard:
    def __init__(self, path, name = 'param_card.dat'):
        self.path = path / 'Cards'
        self.file_spec = self.path / name
        self.blocks = dict()
        self.decays = dict()
        with open(self.file_spec, 'r') as file:
            for line in file:
                t = line.strip()
                if len(t)==0 or t.startswith('#'):
                    continue # ignores comments; who needs those anyway...
                elif t.upper().startswith('BLOCK'):
                    block_key = ParamCard.extract_block_key(t)
                    self.blocks[block_key] = dict()
                elif t.upper().startswith('DECAY'):
                    try:
                        tokens = t.split()
                        self.decays[int(tokens[1])] = BlockEntry(tokens[2], ParamCard.get_comment(t)) 
                    except:
                        print('cannot parse:', t)
                else:
                    try:
                        tokens = t.split()
                        self.blocks[block_key][int(tokens[0])] = BlockEntry(tokens[1], ParamCard.get_comment(t))
                    except:
                        print('cannot parse:', t)
        
    def __repr__(self):
        s = 'Abstract of Parameter Card\n'
        s += '  ' + str(self.file_spec) + '\n    BLOCKS:\n'
        for k,v in self.blocks.items():
            s += '      ' + k + ' (' + str(len(v)) + ')\n'
        s += '    DECAY (' + str(len(self.decays)) + ')\n' 
        return s

    def valid_keys(self):
        return ['DECAY'] + [k for k in self.blocks.keys()]
    
    def extract_block_key(txt):
        if '#' in txt:
            block_key = txt.split('#')[0]
        else:
            block_key = txt
        return block_key.upper().replace('BLOCK ','').strip()
    
    def get_block_entry_dict(self, tag):
        if tag == 'DECAY':
            return self.decays
        else:
            return self.blocks[tag]    

    def df(self, tag):
        try:
            d = self.get_block_entry_dict(tag)
            d = [[k, v.v, v.comment] for k,v in d.items()]
            return pd.DataFrame(d, columns=['key','value','comment'])
        except:
            print('syntax error... try:')
            print('\n  df(\'DECAY\')\n\n  --or--\n')
            for k in self.blocks.keys():
                print('  df(\'' + k + '\')')

    def dfs(self):
        dataframes = {'DECAY': self.df('DECAY')}
        for k in self.blocks.keys():
            dataframes[k] = self.df(k)
        return dataframes
    
    def set_value(self, tag, k, v):
        d = self.get_block_entry_dict(tag)  
        if not k in d.keys():
            print(k + ' does not exist in ' + tag + '; value ignored.')
            return
        d[k].v = v

    def get_value(self, tag, k):
        df = self.dfs()[tag]
        return df[df['key'] == k]

    def set_comment(self, tag, k, comment):
        d = self.get_block_entry_dict(tag)  
        if not k in d.keys():
            print(k + ' does not exist in ' + tag + '; value ignored.')
            return
        d[k].comment = comment

    def get_comment(line):
        if '#' in line:
            return line.split("#")[-1]
        else:
            return ''

    def write(self, path = None, name = 'param_card.out', overwrite = False, no_format = ['QNUMBERS']):
        if path is None:
            path = self.path
        outfile = path / name
        if (not overwrite) and os.path.exists(outfile):
            print(outfile + ' exists and overwrite is set to False')
        try:
            with open(self.file_spec, 'r') as input, open(path / name, 'w') as output:
                for line in input:
                    if line.strip().startswith('#'):
                        continue
                    elif line.strip().upper().startswith('BLOCK'):
                        output.write(line)
                        key = ParamCard.extract_block_key(line) 
                        for k,v in self.blocks[key].items():
                            no_formatting = any([x in line for x in no_format]) # does any no_format token appear in line?
                            if no_formatting:
                                output.write('      ' + str(k) + ' ' + str(int(v.v)) + ' # ' + v.comment + '\n')
                            else:
                                output.write('      ' + str(k) + ' ' + "{:.6e}".format(v.v) + ' # ' + v.comment + '\n')
                    elif line.strip().upper().startswith('DECAY'):
                        key = int(line.strip().split()[1])
                        val = self.decays[key]
                        output.write('DECAY ' + str(key) + ' ' + "{:.6e}".format(val.v) + ' # ' + val.comment + '\n')
        finally:
            output.close()
        print('wrote: ' + str(outfile))
