from helper_functions import *
import json
import jsonlines


if __name__ == "__main__":
    muc = open('data/MUC_raw/MUC_consolodation.json')
    data = json.load(muc)

    # clear the file
    open('data/MUC_converted/MUC_converted.jsonl', 'w').close()

    open('data/MUC_converted/MUC_converted_train.jsonl', 'w').close()
    open('data/MUC_converted/MUC_converted_dev.jsonl', 'w').close()
    open('data/MUC_converted/MUC_converted_test.jsonl', 'w').close()

    for ind in range(0, len(data)):
        json_data = json.dumps(convert_by_ind(data, ind))

        if (json_data == "null"):  # templates with no event
            continue

        msg_id = data[ind]["data"]["template"]["MESSAGE: ID"][:4]
        if msg_id == "DEV-" or msg_id == " DEV":
            with jsonlines.open('data/MUC_converted/MUC_converted_train.jsonl', mode='a') as writer:
                writer.write(json_data)
        elif msg_id == "TST1" or msg_id == "TST2":
            with jsonlines.open('data/MUC_converted/MUC_converted_dev.jsonl', mode='a') as writer:
                writer.write(json_data)
        elif msg_id == "TST3" or msg_id == "TST4":
            with jsonlines.open('data/MUC_converted/MUC_converted_test.jsonl', mode='a') as writer:
                writer.write(json_data)
        else:
            raise Exception("could not recognize message id:", msg_id)

        with jsonlines.open('data/MUC_converted/MUC_converted.jsonl', mode='a') as writer:
            writer.write(json_data)

    muc.close()
