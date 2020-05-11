from character import CHARACTER
from defs import CONV, SING, NARR
from defs import ON_NONE, ON_NARR, ON_CONV, ON_SING, EX_SING, ON_TWOC


# class SCRIPT
#   data of script
#
# content - list of CONV, DESC, TIMEPLACE
#   parsed results
# character - list of CHARACTER
#   characters in the script
class SCRIPT():
    def __init__(self):
        self.content = []
        self.character = []

    # get_character_by_name
    #   check if the chacacter name already shown before
    #   return CHARACTER which has same character name if exist
    #   return None if not exist
    def get_character_by_name(self, character_name):
        fl = list(filter(lambda x: character_name == x.name, self.character))
        if len(fl) == 0:
            return None
        return fl[0]

    # append_content
    #   add contents of script
    def append_content(self, cont):
        if not isinstance(cont, CONV) \
                and not isinstance(cont, TIMEPLACE):
            raise TypeError("content can only have CONV, DESC, TIMEPLACE, not %s" % (type(cont)))
        self.content.append(cont)

    # append_character
    #   add new character
    def append_character(self, character):
        if not isinstance(character, CHARACTER):
            raise TypeError("character can only have CHARACTER, not %s" % (type(cont)))
        self.character.append(character)


# class CONV
#   data of conversation
#
# text - str
#   text data
# type - int
#   0 : conversation
#   1 : sing
#   2 : narrator
#   use defs.CONV, defs.SING, defs.NARR instead of number
# cont - boolean
#   is this continued?
# speak - CHARACTER
#   who is saying
# listen - CHATACTER or None
#   who is listening
# ref - list of CHARACTER
#   link of pronouns
class CONV():
    def __init__(self, text, type, cont, speak):
        self.text = text
        self.type = type
        self.cont = cont
        self.speak = speak
        self.listen = None
        self.ref = []

    def __repr__(self):
        return "<conv {}>".format(self.type)


# class TIMEPLACE
#   data of scene heading
#
# place - str
#   place where scene begin
# time - str
#   time of scene, but not exact time(DAY, DAWN, NIGHT, ...)
class TIMEPLACE():
    def __init__(self, time, place):
        self.time = time
        self.place = place

    def __repr__(self):
        return "<timeplace>"


# parse_playscript
#   parse play script from file
#
# input
#   fp - File Object
#     file pointer to read
# output
#   SCRIPT Object
#     result of parsing script
def parse_playscript(fp):
    script = SCRIPT()

    # find first line
    # *in lazy way*
    while True:
        line = fp.readline().strip()
        if line.startswith("OPEN ON:"):
            break
    script.append_content(TIMEPLACE("", line.split("OPEN ON: ")[1]))

    # automata flag
    # ON_NONE : expecting everything
    # ON_NARR : on narrator
    # ON_CONV : on normal conversation
    # ON_SING : on sing
    # EX_SING : expecting sing
    # ON_TWOC : on two conversation
    am_flag = ON_NONE

    conv = None
    conv2 = None
    before_type = None
    while True:
        line = fp.readline()
        if line == "" or line.strip() == "THE END":  # end script or EOF
            if am_flag != ON_NONE:
                script.append_content(conv)
                if am_flag == ON_TWOC:
                    script.append_content(conv2)
            break
        elif line == "\n":
            if am_flag == ON_TWOC:
                script.append_content(conv)
                script.append_content(conv2)
                before_type = conv.type
                am_flag = ON_NONE
        # seperate in lazy way
        elif line.startswith("                                              "):
            continue  # page number, script signs
        elif line.startswith("                  "):  # conv or sing or sing title
            sline = line[:]
            line = line.strip()
            if line.startswith("\""):  # sing title
                if am_flag != ON_NONE:  # something parsed
                    script.append_content(conv)
                    if am_flag == ON_TWOC:
                        script.append_content(conv2)
                    if am_flag != ON_NARR:
                        before_type = conv.type

                am_flag = EX_SING
            elif am_flag == EX_SING:  # sing - on singer
                character_name = line.split("(", 1)[0].strip()
                # TODO : How to handle "YOUNG" or "TEEN"?
                #      : More information about speaker such as (9)
                character = script.get_character_by_name(character_name)
                if not character:
                    character = CHARACTER(character_name, "")
                    script.append_character(character)
                conv = CONV("",
                            before_type if line.find("(CONT'D)") != -1 else SING,
                            line.find("(CONT'D)") != -1,
                            character)
                am_flag = ON_SING
            elif am_flag == ON_SING:  # sing - on lyrics
                conv.text += ("" if len(conv.text) == 0 else " ") + line
            elif am_flag == ON_CONV and not sline.startswith("                            "):
                conv.text += ("" if len(conv.text) == 0 else " ") + line
            else:  # conv - on speaker
                if am_flag != ON_NONE:  # something parsed
                    script.append_content(conv)
                    if am_flag == ON_TWOC:
                        script.append_content(conv2)
                    if am_flag != ON_NARR:
                        before_type = conv.type

                character_name = line.split("(", 1)[0].strip()
                character = script.get_character_by_name(character_name)
                if not character:
                    character = CHARACTER(character_name, "")
                    script.append_character(character)
                conv = CONV("",
                            before_type if line.find("(CONT'D)") != -1 else CONV,
                            line.find("(CONT'D)") != -1,
                            character)
                am_flag = ON_CONV

        elif line.startswith("   "):  # narrator or time & place
            if line.startswith("    "):
                if am_flag != ON_NONE:
                    script.append_content(conv)
                    if am_flag == ON_TWOC:
                        script.append_content(conv2)
                    if am_flag != ON_NARR:
                        before_type = conv.type

                line = line.strip()
                n1, n2 = line.split("                              ")
                n1 = n1.split("(", 1)[0].strip()
                n2 = n2.split("(", 1)[0].strip()
                character1 = script.get_character_by_name(n1)
                character2 = script.get_character_by_name(n2)
                if not character1:
                    character1 = CHARACTER(character_name, "")
                    script.append_character(character1)
                if not character2:
                    character2 = CHARACTER(character_name, "")
                    script.append_character(character2)
                conv = CONV("",
                            before_type if n1.find("(CONT'D)") != -1 else CONV,
                            n1.find("(CONT'D)") != -1,
                            character1)
                conv2 = CONV("",
                             before_type if n2.find("(CONT'D)") != -1 else CONV,
                             n2.find("(CONT'D)") != -1,
                             character2)
                am_flag = ON_TWOC
                continue
            line = line.strip()
            # TODO : Non standard scene heading.
            #        Starts with -INT. or -EXT. but has some narrator text in
            #        one line
            if line.startswith("EXT. ") or line.startswith("INT. "):  # time
                if am_flag != ON_NONE:  # something parsed
                    script.append_content(conv)
                    if am_flag == ON_TWOC:
                        script.append_content(conv2)
                    if am_flag != ON_NARR:
                        before_type = conv.type

                try:
                    place, time = line.split(". ")[1].split(" -- ")
                except:
                    place, time = line.split(". ")[1].split(" - ")
                script.append_content(TIMEPLACE(time, place))
                am_flag = ON_NONE
            elif am_flag == ON_TWOC:
                txt = line.split("          ")
                if len(txt) == 1:  # only left character
                    conv.text += ("" if len(conv.text) == 0 else " ") + txt[0].strip()
                elif len(txt[0].strip()) == 0:  # only right character
                    conv2.text += ("" if len(conv2.text) == 0 else " ") + txt[-1].strip()
                else:
                    conv.text += ("" if len(conv.text) == 0 else " ") + txt[0].strip()
                    conv2.text += ("" if len(conv2.text) == 0 else " ") + txt[-1].strip()
            elif am_flag == ON_NARR:
                conv.text += ("" if len(conv.text) == 0 else " ") + line
            else:
                if am_flag != ON_NONE:  # something parsed
                    script.append_content(conv)
                    if am_flag == ON_TWOC:
                        script.append_content(conv2)
                    if am_flag != ON_NARR:
                        before_type = conv.type

                conv = CONV(line,
                            NARR,
                            None,
                            None)
                am_flag = ON_NARR
        else:  # title or etc - ignore
            continue
    return script


if __name__ == "__main__":
    f = open("./data/FROZEN.txt")
    script = parse_playscript(f)
    for cont in script.content:
        if isinstance(cont, TIMEPLACE):
            print("TIME : {}, PLACE : {}".format(cont.time, cont.place))
        elif cont.type == NARR:
            print("NARR : {}".format(cont.text))
        else:
            print("{} : {}".format(cont.speak.name, cont.text))
