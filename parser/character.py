from defs import *
from script import *

from tqdm import tqdm
import pickle
import os
import re
import xml.etree.ElementTree as ET
from nltk.tokenize import word_tokenize
from nltk.lm import Vocabulary
from nltk.classify.naivebayes import NaiveBayesClassifier as NB


# class PERSONALITY
#   Big-5 Personality data
class PERSONALITY:
    def __init__(self):
        self.extroverted = 0
        self.stable = 0
        self.agreeable = 0
        self.conscientious = 0
        self.openness = 0

    # get_PERSONALITY
    # return Big 5 Personality value in tuple format
    def get_PERSONALITY(self):
        return [self.extroverted, self.stable, self.agreeable, self.conscientious, self.openness]

    def set_PERSONALITY(self, extroverted, stable, agreeable, conscientious, openness):
        self.extroverted = extroverted
        self.stable = stable
        self.agreeable = agreeable
        self.conscientious = conscientious
        self.openness = openness


class CHARACTERISTIC_TRAINER:
    def __init__(self, savedir=None):
        self.train = {}
        self.test = {}
        self.classifier = {}
        self.vocab = Vocabulary(unk_cutoff=1)
        self.prepare_dataset(mode='train')
        self.prepare_dataset(mode="test")
        self.vocab_words = {w: 0 for w in self.vocab.counts.keys() if w in self.vocab}
        self.vocab_words['UNK'] = 0  # initially add UNK feature section
        # vocab size is currently 20124
        # uncomment this and erase the below line for full training. Currently training only gender for speed issue
        for mode in ['gender', 'age_group', 'extroverted', 'stable', 'agreeable', 'conscientious', 'openness']:
            self.run_train(mode)

        if savedir is not None:
            with open(savedir, 'wb') as f:
                pickle.dump(self, f)
        # self.run_train('gender')

    def prepare_dataset(self, mode="train"):  # mode = ["train", "test"]
        """
        Each line of the truth files encodes the following information:
        userid:::gender:::age_group:::extroverted:::stable:::agreeable:::conscientious:::openness
        """
        print(f"prepare_dataset: {mode} START")
        if mode == "train":
            dir_path = CHAR_TRAIN_DIR
            saved = self.train
        elif mode == "test":
            dir_path = CHAR_TEST_DIR
            saved = self.test
        else:
            raise Exception("Directory name should be one of 'train' or 'test'")

        with open(dir_path + "truth.txt", "r") as f:
            truths = f.read().split('\n')[:-1]
        for truth in truths:
            userid, gender, age_group, extroverted, stable, agreeable, conscientious, openness = truth.split(":::")
            root = ET.parse(f"{dir_path}{userid}.xml").getroot()
            words = [self.preprocess_text(child.text, mode=mode) for child in root]
            saved[userid] = {"gender": gender, "age_group": age_group,
                             "extroverted": float(extroverted), "stable": float(stable),
                             "agreeable": float(agreeable), "conscientious": float(conscientious),
                             "openness": float(openness), "text": words}

        print(f"prepare_dataset: {mode} DONE")

    def preprocess_text(self, text, mode='train'):  # clean up and tokenize text
        processed_text = []
        # remove url
        # change @username to you
        if 'http' in text:
            text = text[:text.index('http')]
        text = re.sub(r"[^A-Z a-z?!-]+", '', text)
        words = [w.lower() for w in word_tokenize(text)]
        if mode == 'train':
            self.vocab.update(words)  # add corresponding word to vocab
        return words

    def get_feature_dict(self, words):
        feature_dict = self.vocab_words.copy()
        for word in words:
            if word in self.vocab:
                feature_dict[word] += 1
            else:
                feature_dict['UNK'] += 1
        return feature_dict

    def run_train(self, mode='agreeable'):
        # mode in ['gender', 'age_group', 'extroverted', 'stable',
        # 'agreeable',·'conscientious', 'openness']
        train_input = []
        print(f"making train_input: {mode}")
        for infos in tqdm(self.train.values()):
            for info in infos['text']:  # process same label for 100 texts
                train_input.append((self.get_feature_dict(info), infos[mode]))
        print(f"running trainer... {mode}")
        self.classifier[mode] = NB.train(train_input)
        print("running trainer done")

    def predict(self, text, mode='gender'):  # mode has to be one of classifier.keys()
        preprocessed_words = self.preprocess_text(text, mode='predict')
        feature_dict = self.get_feature_dict(preprocessed_words)
        classified = self.classifier[mode].classify(feature_dict)
        # print(f"Predicted output: {classified}")
        return classified


# class CHARACTER
#   data of character
#
# inheritance PERSONALITY
#
# name - str
#   character's name
# sex - str
#   character's gender
class CHARACTER(PERSONALITY):
    def __init__(self, name, sex):
        super().__init__()
        self.name = name
        self.sex = sex
        self.age_group = None


def extract_personality(script, pretrained=None):
    if pretrained is None or not os.path.exists(pretrained):
        trainer = CHARACTERISTIC_TRAINER(savedir=pretrained)
    else:
        with open(pretrained, 'rb') as f:
            trainer = pickle.load(f)

    for character in script.character:
        text_character = [content.text for content in script.content if isinstance(content, CONV) and
                          content.speak == character]
        len_text = len(text_character)
        personality = character.get_PERSONALITY()
        gender = []
        age_group = []
        for text in text_character:
            gender.append(trainer.predict(text, mode='gender'))
            age_group.append(trainer.predict(text, mode='age_group'))
            for i, mode in enumerate(['extroverted', 'stable', 'agreeable', 'conscientious', 'openness']):
                personality[i] += trainer.predict(text, mode=mode) / len_text
        character.gender = max(set(gender), key=gender.count)
        character.age_group = max(set(age_group), key=age_group.count)
        character.set_PERSONALITY(*personality)


if __name__ == "__main__":
    # trainer = CHARACTERISTIC_TRAINER()
    # trainer.predict('I am so hungry !', mode='gender')
    with open("./data/FROZEN.txt", "r") as f:
        script = parse_playscript(f)
    extract_personality(script, './characteristic_trainer.pickle')
    for chr in script.character:
        print(f'{chr.name}: {chr.gender}/{chr.age_group}/{chr.get_PERSONALITY()}')
    with open('script_frozen.pickle', 'wb') as f:
        pickle.dump(script, f)

