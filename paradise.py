# paradise implementation in python

import os


COMMANDS = {
    "create": "Create a new vessel at your current location.",
    "enter": "Enter a visible vessel.",
    "leave": "Exit the parent vessel.",
    "become": "Become a visible vessel.",
    "take": "Move a visible vessel into a child vessel.",
    "drop": "Move a child vessel into the parent vessel.",
    "warp": "Move to a distant vessel.",
    "note": "Add a description to the current parent vessel.",
    "pass": "Add a passive note to the current parent vessel.",
    "program": "Add an automation program to a vessel, making it available to the use command.",
    "learn": "Read documentation for each action, or see a list of action.",
    "use": "Trigger a vessel's program.",
    "transform": "Change your current vessel name.",
    "move": "Move a visible vessel into another visible vessel.",
    # new commands
    "destroy": "Destroy a vessel.",
    "context": "Get the current context.",
    "exit": "Exit this universe."
}

IGNORE_COMMANDS = [
    "a",
    "to",
    "the"
]

HELP_NOTE = "welcome to the library, you can edit this message with the {note} action. to begin, make a new vessel with {create}. type {learn} to see the list of commands."


def getValueFromKey(d, k, retIfNone=None):
    try:
        return d[k]
    except KeyError:
        return retIfNone

# merge d1 into d2 (replace)
def mergeDicts(d1, d2):
    for k in d2.keys():
        try:
            d2[k] = d1[k]
        except KeyError:
            pass

    return d2

def untilStopperChar(args, index):
    stopperChars = ["&"]

    for i in range(index, len(args)):

        arg = args[i]

        if arg in stopperChars:
            return args[index:i], i

    return args[index:], len(args)

def getVessel(lst, name):
    for i, l in enumerate(lst):
        if name == str(l):
            return l, i

    return None, None

class Context:
    def __init__(self):
        self.root = Vessel("library", note=HELP_NOTE)
        self.within = self.root
        self.vessel = Vessel("ghost")
        self.parents = []

class Vessel:
    def __init__(self, name, note="", passive="", program="", children=[], inventory=[]):
        self.name = name
        self.note = note
        self.passive = passive
        self.program = program
        self.children = children
        self.inventory = inventory

    def clone(self):
        return Vessel(self.name, self.note, self.passive, self.program, self.children, self.inventory)

    def __str__(self):
        return self.name

context = Context()
displaytext = ""
meta = {"saycontext": True}

def paradiseTokenizer(cmd=""):
    tokenized = []
    commands = cmd.split("&")

    for c in commands:
        preprocessed = c.strip().split(" ")

        args = []

        for p in preprocessed:
            if p not in IGNORE_COMMANDS:
                args.append(p)

        if args[0] in COMMANDS.keys():
            cmd = args.pop(0)

            if cmd == "move":
                temp = " ".join(args)

                temp = temp.split("into")

                if len(temp) > 1:
                    args = temp

                for i, v in enumerate(args):
                    args[i] = v.strip()

                tokenized.append(["move"] + args)
            else:
                tokenized.append([f"{cmd}", " ".join(args)])
        else:
            tokenized.append(["PLAINTEXT", " ".join(args)])

    return tokenized

def paradiseParser(cmds=[]):
    global displaytext

    toreturn = []

    for cmdblock in cmds:
        cmd = cmdblock[0]
        arg = cmdblock[1]

        match cmd:
            case "exit" | "quit":
                quit()
            case "PLAINTEXT":
                toreturn.append(f'You said "{arg}".')
            case "create":
                vessel = getVessel(context.within.children, arg)[0]

                if vessel:
                    toreturn.append(f"You cannot create another {vessel}.")
                else:
                    context.within.children.append(Vessel(arg, children=[]))
                    toreturn.append(f"You created the {arg}.")
            case "enter":
                vessel = getVessel(context.within.children, arg)[0]

                if vessel:
                    context.parents.append(context.within)
                    context.within = vessel

                    toreturn.append({"text": f"You entered the {context.within}.", "saycontext": True})
                else:
                    toreturn.append("You do not see the target vessel.")
            case "leave":
                if context.parents:
                    oldname = context.within.name
                    context.within = context.parents.pop()

                    toreturn.append({"text": f"You left the {oldname}.", "saycontext": True})
                else:
                    toreturn.append("You cannot leave a paradox.")
            case "become":
                vessel, index = getVessel(context.within.children, arg)

                if vessel:
                    oldvessel = context.vessel
                    context.vessel = vessel
                    context.within.children.pop(index)
                    context.within.children.append(oldvessel)
                    toreturn.append(f"You became the {vessel}.")
            case "take":
                vessel, index = getVessel(context.within.children, arg)

                if vessel:
                    context.within.inventory.append(vessel)
                    context.within.children.pop(index)
                else:
                    toreturn.append("You do not see the target vessel.")
            case "drop":
                vessel, index = getVessel(context.within.inventory, arg)

                if vessel:
                    context.within.children.append(vessel)
                    context.within.inventory.pop(index)
                else:
                    toreturn.append("You do not see the target vessel.")
            case "warp":
                def parentsSearch(parents, name):
                    for p in parents:
                        print(f"parent: {p}")
                        for i, c in enumerate(p.children):
                            print(f"child: {c}")
                            if c.name == name:
                                return c
                        if p.name == name:
                            return p
                    return None 
                    
                vessel = parentsSearch(context.parents, arg)

                if vessel:
                    context.within = vessel
                    toreturn.append({"text": f"You warped into the {vessel}.", "saycontext": True})
                else:
                    toreturn.append("You do not see the target vessel.")
            case "note":
                context.within.note = arg
            case "pass":
                context.within.passive = arg
            case "program":
                context.within.program = arg
            case "learn":
                try:
                    toreturn.append(COMMANDS[cmdblock[1]])
                except IndexError:
                    toreturn.append("learn topic not provided")
            case "use":
                vessel, index = getVessel(context.within.children, arg)

                if vessel:
                    toreturn = toreturn + paradiseParser(paradiseTokenizer(vessel.program))
                else:
                    toreturn.append("You do not see the target vessel.")
            case "transform":
                context.within.name = arg
                toreturn.append(f"You transformed into a {arg}.")
            case "move":
                origvessel, oindex = getVessel(context.within.children, arg)

                if origvessel:
                    try:
                        intovessel, index = getVessel(context.within.children, cmdblock[2])

                        if intovessel:
                            intovessel.children.append(context.within.children.pop(oindex))

                            toreturn.append(f"You moved the {origvessel} into {intovessel}.")
                        else:
                            toreturn.append(f"Missing {intovessel}.")
                    except IndexError:
                        toreturn.append(f"Move {origvessel} into what?")
                else:
                    toreturn.append(f"Missing {origvessel}.")

            case "destroy":
                vessel, index = getVessel(context.within.children, arg)

                if vessel:
                    context.within.children.pop(index)
                    toreturn.append(f"You destroyed the {vessel}.")
                else:
                    toreturn.append("You do not see the target vessel.")
            case "context":
                toreturn.append({"saycontext": True})
            case _:
                pass

    return toreturn
def paradise():
    global displaytext, meta

    os.system("clear")    

    while True:
        canSayContext = type(meta) is dict and getValueFromKey(meta, "saycontext")

        if canSayContext:
            print(f"you are a {context.vessel.name}, in the {context.within.name}.\n")

            if context.within.note:
                print(context.within.note + "\n")

            if context.within.children:
                for v in context.within.children:
                    print(f"   - enter the {v}")
                print()

        if displaytext:
            print(displaytext + "\n")

        if canSayContext:
            if context.within.inventory:
                for i in context.within.inventory:
                    print(f"   - drop the {i}")
                print()

        out = paradiseParser(paradiseTokenizer(input("> ")))

        if out:
            meta = out[-1]

            if type(meta) is str:
                displaytext = meta
            else:
                displaytext = getValueFromKey(meta, "text", "")
        else:
            displaytext = ""


if __name__ == "__main__":
    paradise()
