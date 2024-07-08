from helper_functions import *
import IPython
import json
from nltk.tokenize.treebank import TreebankWordDetokenizer


def sort_by_start_ind(ent):
    return ent[0]


def gen_html(data, ind):
    dictionary = convert_by_ind(data, ind)
    if (dictionary is None):
        f = open('visual_test.html', 'w')
        html_template = """
    <html>
    <head>
    </head>
    <body>
      <h1> No Trigger </h1>
    </body>
    </html>
    """
        f.write(html_template)
        f.close()
        return

    tokenized_text = dictionary["sentences"]
    tokenized_concat = []
    for sentence in tokenized_text:
        for word in sentence:
            tokenized_concat.append(word)

    items_inserted = 0

    ent_spans = dictionary["ent_spans"]
    ent_spans.append(dictionary["evt_triggers"][0])
    ent_spans.sort(key=sort_by_start_ind)

    for ent in ent_spans:
        start_ind = ent[0]
        end_ind = ent[1] + 1  # end index is inclusive
        role_str = ent[2][0][11:]

        if (role_str == "attacker"):
            color = "purple"
        elif (role_str == "instrument"):
            color = "blue"
        elif (role_str == "target"):
            color = "pink"
        elif (role_str == "victim"):
            color = "green"
        else:  # trigger
            color = "yellow"

        opening_tag = "<mark style=\"background-color:" + color + ";\">"
        closing_tag = "</mark>"

        tokenized_concat.insert(start_ind + items_inserted, opening_tag)
        items_inserted += 1
        tokenized_concat.insert(end_ind + items_inserted, closing_tag)
        items_inserted += 1

    untokenized_text = TreebankWordDetokenizer().detokenize(tokenized_concat)

    f = open('visual_test.html', 'w')
    html_template = """
  <html>
  <head>
  <style>
    .key {padding: 5px; width: 100px; text-align: center;}
  </style>
  </head>
  <body>
    <h1 style="text-align: center;"> ID #""" + str(data[ind]["id"]) + """ </h1>
    <h2 style="text-align: center;"> Full Text </h2>
    <p id="text"> """ + data[ind]["data"]["text"] + """ </p>
    <h2 style="text-align: center;"> Template Details </h2>
    <h4> INCIDENT: INSTRUMENT ID: """ + data[ind]["data"]["template"]["INCIDENT: INSTRUMENT ID"] + """ </h4>
    <h4> PERP: INDIVIDUAL ID: """ + data[ind]["data"]["template"]["PERP: INDIVIDUAL ID"] + """ </h4>
    <h4> PERP: ORGANIZATION ID: """ + data[ind]["data"]["template"]["PERP: ORGANIZATION ID"] + """ </h4>
    <h4> PHYS TGT: ID: """ + data[ind]["data"]["template"]["PHYS TGT: ID"] + """ </h4>
    <h4> HUM TGT: NAME: """ + data[ind]["data"]["template"]["HUM TGT: NAME"] + """ </h4>
    <h4> HUM TGT: DESCRIPTION: """ + data[ind]["data"]["template"]["HUM TGT: DESCRIPTION"] + """ </h4>
    <h2 style="text-align: center;"> Key </h2>
    <div style="display: flex; flex-direction: row; justify-content: space-around; border: 1px solid black; padding: 15px;">
      <p class="key" style="background-color: yellow;"> Middle Trigger </p>
      <p class="key" style="background-color: blue;"> Instrument </p>
      <p class="key" style="background-color: pink;"> Target </p>
      <p class="key" style="background-color: purple;"> Attacker </p>
      <p class="key" style="background-color: green;"> Victim </p>
    </div>
    <p> """ + untokenized_text + """ </p>
  </body>
  </html>
  """

    f.write(html_template)
    f.close()


if __name__ == "__main__":

    f = open('data/MUC_raw/MUC_consolodation.json')
    data = json.load(f)
    gen_html(data, 102)

    f.close()
    IPython.display.HTML(filename='visual_test.html')
