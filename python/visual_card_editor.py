import ipywidgets as widgets
from IPython.display import display 

def edit_card(framework_path, comment_delim='#', card_name='run_card.dat'):  # Returns list of lines in card 
    global cards_path
    cards_path = framework_path / 'Cards/'
    with open(cards_path / card_name, 'r') as file:
        lines = file.readlines()
    card = [line.strip() for line in lines]
    sep_card = seperate_comments(card, comment_delim)
    return display_card(sep_card, cards_path / card_name)

def edit_card_spec(card_spec, comment_delim='#'): 
    with open(card_spec, 'r') as file:
        lines = file.readlines()
    card = [line.strip() for line in lines]
    sep_card = seperate_comments(card, comment_delim)
    return display_card(sep_card, card_spec)

def seperate_comments(card_by_line, delim):
    card_seperated = []
    for line in card_by_line:
        if len(line) == 0 or line[0] == delim:  # Leave comment/empty lines as string 
            card_seperated.append(line)
        else:   # Make non-comments lines into editable widgets 
            card_seperated.append(widgets.Text(value=line, layout=widgets.Layout(width='550px')))
    return card_seperated

def display_card(seperated_card, file_path):
    for line in seperated_card:
        if isinstance(line, str):
            print(line)
        else:
            display(line)
    # Display save button
    button = widgets.Button(description="Save")
    output = widgets.Output()
    display(button, output)

    def on_button_clicked(b):
        with output:
            print("Saving...")
        write_card(file_path, seperated_card, output)

    # Bind the button click event
    button.on_click(on_button_clicked)

def write_card(file_path, seperated_card, output):
    with open(file_path, 'w') as file:  # Change 'r' to 'w' for writing
        for line in seperated_card:
            if isinstance(line, str):
                file.write(line + '\n')  # Add newline after each line
            else:
                file.write(line.value + '\n')
        #file.write('0 = madanalysis5  # Disable MadAnalysis 5\n')

    with output:  # Use the same output widget
        print('Saved')

def get_cards_path():
    return cards_path