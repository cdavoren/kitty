#!/usr/bin/env python3

"""
Intended to be used with the Gogh themes located at https://mayccoll.github.io/Gogh/
"""

import argparse, sys, glob, re, os


def hex_to_rgb(hex_str):
    if hex_str[0] == '#':
        hex_str = hex_str[1:]

    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)

    return (r, g, b)

BRIGHTEN_ADJUSTMENT = 24
DARKEN_ADJUSTMENT = -24

def adjust_color(rgb_tuple, adjustment):
    rgb = [rgb_tuple[0], rgb_tuple[1], rgb_tuple[2]]
    rgb = [x+adjustment for x in rgb]
    rgb = [int(x) for x in rgb]
    rgb = [min([255, max([0, x])]) for x in rgb]
    return (rgb[0], rgb[1], rgb[2])

class KittyTheme():

    ansi_color_mappings = {
        0 : [6],
        1 : [8],
        2 : [10],
        3 : [12],
        4 : [14],
        5 : [16],
        6 : [18],
        7 : [20],
        8 : [7],
        9 : [9],
        10 : [11],
        11 : [13],
        12 : [15],
        13 : [17],
        14 : [19],
        15 : [21],
    }

    def __init__(self):
        self.colors = {}

    def set_color(self, ansi_color_index, color_tuple):
        for j in KittyTheme.ansi_color_mappings[ansi_color_index]:
            self.colors[j] = color_tuple

    def set_foreground(self, color_tuple):
        self.colors[0] = color_tuple

    def set_background(self, color_tuple):
        self.colors[2] = color_tuple

    def set_cursor(self, color_tuple):
        self.colors[4] = color_tuple

    def complete_colors(self):
        if 0 in self.colors:
            if 1 not in self.colors:
                self.colors[1] = adjust_color(self.colors[0], BRIGHTEN_ADJUSTMENT)
        else:
            self.colors[0] = self.colors[21] # Foreground
            self.colors[1] = adjust_color(self.colors[15], BRIGHTEN_ADJUSTMENT) # Foreground BOLD

        if 2 in self.colors:
            if 3 not in self.colors:
                self.colors[3] = adjust_color(self.colors[2], BRIGHTEN_ADJUSTMENT)
        else:
            self.colors[2] = self.colors[6] # Background
            self.colors[3] = self.colors[7] # Background BOLD

        if 4 in self.colors:
            if 5 not in self.colors:
                self.colors[5] = adjust_color(self.colors[4], BRIGHTEN_ADJUSTMENT)
        else:
            self.colors[4] = self.colors[0] # Cursor text
            self.colors[5] = self.colors[1] # Cursor colour

        # For these to be used, the option "Underlined text is a different colour" must be checked in the Window/Colours option pane
        self.colors[22] = adjust_color(self.colors[0], DARKEN_ADJUSTMENT) # Foreground underlined
        self.colors[23] = adjust_color(self.colors[2], DARKEN_ADJUSTMENT) # Background underlined

        self.colors[24] = adjust_color(self.colors[7], DARKEN_ADJUSTMENT) # Black underlined
        self.colors[25] = adjust_color(self.colors[9], DARKEN_ADJUSTMENT) # Red underlined
        self.colors[26] = adjust_color(self.colors[11], DARKEN_ADJUSTMENT) # Green underlined
        self.colors[27] = adjust_color(self.colors[13], DARKEN_ADJUSTMENT) # Yellow underlined
        self.colors[28] = adjust_color(self.colors[15], DARKEN_ADJUSTMENT) # Blue underlined
        self.colors[29] = adjust_color(self.colors[17], DARKEN_ADJUSTMENT) # Magenta underlined
        self.colors[30] = adjust_color(self.colors[19], DARKEN_ADJUSTMENT) # Cyan underlined
        self.colors[31] = adjust_color(self.colors[21], DARKEN_ADJUSTMENT) # White underlined

        # For these to be used the option "Selected text is a different colour" must be checked in the Window/Colours option pane
        # There appears to be no equivalent in the Gogh themes for this (recommend leaving it unchecked)

        # self.colors[33] # Selected text foreground
        # self.colors[34] # Selected text background

    def __str__(self):
        s = ''
        indices = sorted(self.colors.keys(), reverse=True)
        for index in indices:
            s += "Colour{}\\{},{},{}\\\n".format(index, self.colors[index][0], self.colors[index][1], self.colors[index][2])
        return s

class GoghTheme():

    # COLOR_PATTERN = r"export COLOR_([0-9]{2})='\#([0-9a-f]{6})'"
    COLOR_PATTERN = r'export COLOR_(?P<color_num>[0-9]{2})="?(#*(?P<color_value>[0-9a-fA-F]{6})|\$COLOR_(?P<color_ref>[0-9]{2}))"?'

    BASH_COLOR_OR_VARIABLE = r'"?\$COLOR_(?P<color_num>[0-9]{2})|"#(?P<color_value>[0-9a-fA-F]{6})"|"*\$(?P<variable_name>[A-Z0-9_]*)"?'
    FOREGROUND_PATTERN = r'export FOREGROUND_COLOR=({})'.format(BASH_COLOR_OR_VARIABLE)
    BACKGROUND_PATTERN = r'export BACKGROUND_COLOR=({})'.format(BASH_COLOR_OR_VARIABLE)
    CURSOR_PATTERN = r'export CURSOR_COLOR=({})'.format(BASH_COLOR_OR_VARIABLE)

    def __init__(self):
        self.color_dict = {}

    def set_color(self, value_dict):
        num = int(value_dict['color_num'])
        if value_dict['color_ref'] is not None:
            self.set_color_ref(num, int(value_dict['color_ref']))
        elif value_dict['color_value'] is not None:
            self.set_color_value(num, value_dict['color_value'])

    def set_color_value(self, color_num, color_value):
        self.color_dict[int(color_num)] = hex_to_rgb(color_value)

    def set_color_ref(self, color_num, ref):
        self.color_dict[color_num] = self.color_dict[ref]

    def transfer_value(self, from_name, to_name):
        from_value = None
        if from_name == 'FOREGROUND_COLOR':
            from_value = self.color_dict['foreground']
        elif from_name == 'BACKGROUND_COLOR':
            from_value = self.color_dict['background']
        elif from_name == 'CURSOR_COLOR':
            from_value = self.color_dict['cursor']
        self.color_dict[to_name] = from_value

    def set_value(self, value_dict, dest_key):
        if value_dict['color_value'] is not None:
            self.color_dict[dest_key] = hex_to_rgb(value_dict['color_value'])
        elif value_dict['variable_name'] is not None:
            self.transfer_value(value_dict['variable_name'], dest_key)
        elif value_dict['color_num'] is not None:
            self.color_dict[dest_key] = self.color_dict[int(value_dict['color_num'])]

    def set_foreground(self, value_dict):
        self.set_value(value_dict, 'foreground')

    def set_background(self, value_dict):
        self.set_value(value_dict, 'background')

    def set_cursor(self, value_dict):
        self.set_value(value_dict, 'cursor')

    def read_from_line(self, line_string):
        # Individual colors
        m = re.search(GoghTheme.COLOR_PATTERN, line_string)
        if m is not None:
            value_dict = m.groupdict()
            print('    COLOR {}'.format(value_dict))
            self.set_color(value_dict)
            return
       
        # Foreground color
        m = re.search(GoghTheme.FOREGROUND_PATTERN, line_string)
        if m is not None:
            value_dict = m.groupdict()
            print('    FOREGROUND {}'.format(value_dict))
            self.set_foreground(value_dict)
            return

        # Background color
        m = re.search(GoghTheme.BACKGROUND_PATTERN, line_string)
        if m is not None:
            value_dict = m.groupdict()
            print('    BACKGROUND {}'.format(value_dict))
            self.set_background(value_dict)
            return 

        m = re.search(GoghTheme.CURSOR_PATTERN, line_string)
        if m is not None:
            value_dict = m.groupdict()
            print('    CURSOR {}'.format(value_dict))
            self.set_cursor(value_dict)
            return

    def to_kitty(self):
        kt = KittyTheme()
        for key, value in self.color_dict.items():
            if key == 'foreground':
                kt.set_foreground(value)
            elif key == 'background':
                kt.set_background(value)
            elif key == 'cursor':
                kt.set_cursor(value)
            else:
                kt.set_color(int(key) - 1, value)
        kt.complete_colors()
        return kt

    def __str__(self):
        return str(self.color_dict)

def process_file(open_file, dest_file):
    theme = GoghTheme()
    for line in open_file:
        line = line.strip()
        theme.read_from_line(line)
    
    print(theme)
    kt = theme.to_kitty()
    print(kt, file=dest_file)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('import_path')
    parser.add_argument('export_path')
    args = parser.parse_args()

    file_list = glob.glob(os.path.join(args.import_path, '*.sh'))

    for filename in file_list:
        print('====== {} ======'.format(filename))
        dest_filename = os.path.join(args.export_path, os.path.splitext(os.path.basename(filename))[0] + '.kitty')
        dest_file = open(dest_filename, 'w+')
        f = open(filename, 'r')
        process_file(f, dest_file)
        f.close()
        dest_file.close()

if __name__ == '__main__':
    main()
