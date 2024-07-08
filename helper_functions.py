import spacy
import nltk.data

nltk.download('punkt')
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
nlp = spacy.load('en_core_web_sm')


def format_template(s):
    '''
    Fits the raw instrument text to a pretty format.
    Examples
      Before: "CAR BOMB"; "300 KG OF DYNAMITE" / "DYNAMITE"
      After: [[['CAR', 'BOMB']], [['300', 'KG', 'OF', 'DYNAMITE'], ['DYNAMITE']]]
      Before: "MACHINEGUN"
      After: [[['MACHINEGUN']]]
    '''
    s = s.replace('\"', '')  # remove quotes
    arr = s.split("; ")
    for x in range(0, len(arr)):
        arr[x] = arr[x].split(" / ")
    for x in range(0, len(arr)):
        for y in range(0, len(arr[x])):
            arr[x][y] = ([token.text for token in nlp(arr[x][y])])
    return arr


def gen_ent_span(template_id, role_str, ent_spans, all_sentences, incident_type):
    '''
    Generates an entity span for a given template id and role string.
    Example: gen_ent_span(["data"]["template"]["INCIDENT: INSTRUMENT ID"], "instrument")
    '''
    obj = format_template(template_id)
    if (obj != [[['-']]] and obj != [[['*']]]):
        for i in obj:
            for j in i:
                for k in range(0, len(j)):
                    if j[k] not in all_sentences:
                        break
                    if k == len(j) - 1:
                        start_ind = all_sentences.index(j[0])
                        end_ind = start_ind + len(j) - 1

                        if (incident_type == "ATTACK" or incident_type == "KIDNAPPING" or incident_type == "FORCED WORK STOPPAGE"):
                            evt_num_str = "004"
                        elif (incident_type == "ARSON"):
                            evt_num_str = "012"
                        elif (incident_type == "BOMBING"):
                            evt_num_str = "007"
                        elif (incident_type == "HIJACKING" or incident_type == "ROBBERY"):
                            evt_num_str = "014"
                        else:
                            raise Exception(
                                "unknown incident type:", incident_type)

                        if role_str == "attacker":
                            arg_str = "01"
                        elif role_str == "target":
                            arg_str = "02"
                        elif role_str == "instrument":
                            arg_str = "03"
                        elif role_str == "place":
                            arg_str = "04"
                        elif role_str == "victim":
                            arg_str = "05"
                        else:
                            raise Exception("unknown role string:", role_str)

                        evt_arg_role_str = "evt" + evt_num_str + "arg" + arg_str + role_str
                        # only add argument if no previous argument exists
                        # ex. there shouldn't be 2+ instrument arguments
                        if ent_spans == []:
                            ent_spans.append(
                                [start_ind, end_ind, [evt_arg_role_str, 1.0]])
                        else:
                            for e in range(0, len(ent_spans)):
                                if ent_spans[e][2][0] == evt_arg_role_str:
                                    break
                                if (e == len(ent_spans) - 1):
                                    ent_spans.append(
                                        [start_ind, end_ind, [evt_arg_role_str, 1.0]])

    return ent_spans


def gen_evt_span(incident_type, all_sentences, trigger, trigger_sentence_ind, dictionary, sentence_arr):
    if (incident_type == "ATTACK" or incident_type == "KIDNAPPING" or incident_type == "FORCED WORK STOPPAGE"):
        event_type_str = "conflict.attack.n/a"
    elif (incident_type == "ARSON"):
        event_type_str = "conflict.attack.setfire"
    elif (incident_type == "BOMBING"):
        event_type_str = "conflict.attack.bombing"
    elif (incident_type == "HIJACKING" or incident_type == "ROBBERY"):
        event_type_str = "conflict.attack.stealrobhijack"
    else:
        raise Exception("unknown incident type:", incident_type)

    # get trigger index
    # trigger_arr = trigger.split(" ")
    trigger_arr = trigger
    # accounts for common, possibly repeated words like "bomb" or "killed"
    start_ind = 0
    if (trigger_sentence_ind > 2):
        trigger_sentence_ind = 2
    for i in range(0, trigger_sentence_ind):
        start_ind += len(sentence_arr[i])

    start_ind = all_sentences.index(trigger_arr[0], start_ind)
    end_ind = start_ind + len(trigger_arr) - 1

    dictionary["evt_triggers"] = [
        [start_ind, end_ind, [[event_type_str, 1.0]]]]
    return dictionary


def gen_gold_evt_links(d):
    gold_evt_links = []

    evt_triggers = d["evt_triggers"]
    trigger_start = evt_triggers[0][0]
    trigger_end = evt_triggers[0][1]

    ent_spans = d["ent_spans"]
    for e in ent_spans:
        ent_start = e[0]
        ent_end = e[1]
        role_str = e[2][0]

        gold_evt_links.append([[trigger_start, trigger_end], [
                              ent_start, ent_end], role_str])

    d["gold_evt_links"] = gold_evt_links


def convert_by_ind(data, ind):
    # construct dictionary
    dictionary = {}

    # add the easy keys
    dictionary["doc_key"] = data[ind]["id"]
    dictionary["source_url"] = ""  # not sure if we need this?

    msg_id = data[ind]["data"]["template"]["MESSAGE: ID"][:4]
    if msg_id == "DEV-" or msg_id == " DEV":
        dictionary["split"] = "train"
    elif msg_id == "TST1" or msg_id == "TST2":
        dictionary["split"] = "dev"
    elif msg_id == "TST3" or msg_id == "TST4":
        dictionary["split"] = "test"
    else:
        raise Exception("could not recognize message id:", msg_id)

    # create array of sentences
    text = data[ind]["data"]["text"].replace('\n', ' ')
    sentence_arr = tokenizer.tokenize(text)

    # templates without a trigger
    if (data[ind]["data"]["template"]["INCIDENT: TYPE"] == "*" or data[ind]["data"]["template"]["INCIDENT: TYPE"] == " *"):
        return

    # get middle trigger for consolodation
    baseline = []
    for d in data[ind]["annotations"][0]["result"]:
        try:
            if d["value"]["labels"][0] == "baseline":
                baseline.append(d["value"]["text"])
        except:  # handles checkbox annotations
            continue

    if (baseline != []):
        middle_ind = len(baseline) // 2
        middle_trigger = baseline[middle_ind]
        middle_trigger = middle_trigger.replace('\\n', ' ')

    # tokenize each sentence in the sentence array
    for x in range(0, len(sentence_arr)):
        sentence_arr[x] = ([token.text for token in nlp(sentence_arr[x])])

    # find location of trigger in sentence array
    trigger_sentence_ind = -1
    middle_trigger = ([token.text for token in nlp(middle_trigger)])
    # a little problematic for common words like "attack", "bomb" etc
    # will find the first instance of the word
    for sentence in sentence_arr:
        for i in range(0, len(middle_trigger)):
            if middle_trigger[i] not in sentence:
                break
            if i == len(middle_trigger) - 1:
                trigger_sentence_ind = sentence_arr.index(sentence)
                break

    if trigger_sentence_ind == -1:
        raise Exception("trigger could not be located in any sentence?")

    if (trigger_sentence_ind < 2):
        start_ind = 0
    else:
        start_ind = trigger_sentence_ind - 2
    # truncate sentence array to 5 sentences (2 before and 2 after trigger)
    sentence_arr = sentence_arr[start_ind:trigger_sentence_ind + 3]

    # add the sentence_arr to our dictionary
    dictionary["sentences"] = sentence_arr

    # transform 2D array to 1D array
    # Example:
    # Before: [["Pretend" "this" "is" "one" "sentence"], ["This", "is", "a", "second", "sentence"]]
    # After: ["Pretend" "this" "is" "one" "sentence", "This", "is", "a", "second", "sentence"]
    all_sentences = []
    for sentence in sentence_arr:
        for word in sentence:
            all_sentences.append(word)

    ent_spans = []
    incident_type = data[ind]["data"]["template"]["INCIDENT: TYPE"]

    # ids = [["INCIDENT: INSTRUMENT ID", "instrument"], ["PERP: INDIVIDUAL ID", "attacker"], ["PERP: ORGANIZATION ID", "attacker"], ["PHYS TGT: ID", "target"], ["HUM TGT: NAME", "victim"], ["HUM TGT: DESCRIPTION", "victim"]]
    # not including human target description below
    ids = [["INCIDENT: INSTRUMENT ID", "instrument"], ["PERP: INDIVIDUAL ID", "attacker"], ["PERP: ORGANIZATION ID",
                                                                                            "attacker"], ["PHYS TGT: ID", "target"], ["HUM TGT: NAME", "victim"], ["INCIDENT: LOCATION", "place"]]
    for id in ids:
        ent_spans = gen_ent_span(
            data[ind]["data"]["template"][id[0]], id[1], ent_spans, all_sentences, incident_type)

    dictionary["ent_spans"] = ent_spans

    dictionary = gen_evt_span(data[ind]["data"]["template"]["INCIDENT: TYPE"],
                              all_sentences, middle_trigger, trigger_sentence_ind, dictionary, sentence_arr)

    gen_gold_evt_links(dictionary)

    return dictionary
