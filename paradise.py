# paradise implementation in python

import os
import json

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
    "observe": "Get the current context.",
    "universe": "Create a new universe, with a vessel name as root, or warp to an existing universe.",
    "heatdeath": "Destroy a universe.",
    "multiverse": "Get a list of all universes.",
    "import": "Import a universe JSON file.",
    "export": "Export the current universe as a JSON file.",
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
    def __init__(self, rootname="library", note=""):
        self.host = Vessel(rootname, note=note)
        self.vessel = Vessel("ghost")
        self.parents = []

    def export(self):
        parents = []
        exp = {}

        for p in self.parents:
            parents.append(p.export())

        return {
            "host": self.host.export(),
            "vessel": self.vessel.export(),
            "parents": parents
        }

    def imprt(self, data):
        self.host = Vessel("")
        self.vessel = Vessel("")
        self.parents = []

        for k in data.keys():
            if k == "host":
                self.host.imprt(data[k])
            elif k == "vessel":
                self.vessel.imprt(data[k])
            elif k == "parents":
                for p in data[k]:
                    v = Vessel("")
                    v.imprt(p)
                    self.parents.append(v)

class Vessel:
    def __init__(self, name, note="", passive="", program="", children=None, inventory=None):
        self.name = name
        self.note = note
        self.passive = passive
        self.program = program
        self.children = children or []
        self.inventory = inventory or []

    def clone(self):
        return Vessel(self.name, self.note, self.passive, self.program, self.children, self.inventory)

    def imprt(self, data):
        self.name, self.note, self.passive, self.program, self.children, self.inventory = "", "", "", "", [], []

        for k in data.keys():
            if k == "name":
                self.name = data[k]
            elif k == "note":
                self.note = data[k]
            elif k == "passive":
                self.passive = data[k]
            elif k == "program":
                self.program = data[k]
            elif k == "children":
                for c in data[k]:
                    v = Vessel("")
                    v.imprt(c)
                    self.children.append(v)
            elif k == "inventory": 
                for i in data[k]:
                    v = Vessel("")
                    v.imprt(i)
                    self.inventory.append(i)

    def export(self):
        children = []
        inventory = []
        exp = {}

        for c in self.children:
            children.append(c.export())

        for i in self.inventory:
            inventory.append(i.export())

        exp["name"] = self.name

        if self.note:
            exp["note"] = self.note

        if self.passive:
            exp["passive"] = self.passive

        if self.program:
            exp["program"] = self.program

        if children:
            exp["children"] = children
        
        if inventory:
            exp["inventory"] = inventory

        return exp

    def __str__(self):
        return self.name

displaytext = ""
meta = {"saycontext": True}
universes = [Context("library", HELP_NOTE)]
context = universes[0]

def paradiseTokenizer(cmd=""):
    tokenized = []
    commands = cmd.split("&")

    for c in commands:
        preprocessed = c.strip().split(" ")

        args = []

        if preprocessed[0] in ["note", "pass", "program"]:
            args = preprocessed
        else:
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
    global displaytext, context, universes

    toreturn = []

    for cmdblock in cmds:
        cmd = cmdblock[0]
        arg = cmdblock[1]

        match cmd:
            case "exit" | "quit":
                quit()
            case "PLAINTEXT":
                toreturn.append(f'You said "{arg}".') # FIX: still removes a, to, the
            case "create":
                vessel = getVessel(context.host.children, arg)[0]

                if vessel:
                    toreturn.append(f"You cannot create another {vessel}.")
                else:
                    context.host.children.append(Vessel(arg, children=[]))
                    toreturn.append(f"You created the {arg}.")
            case "enter":
                vessel = getVessel(context.host.children, arg)[0]

                if vessel:
                    context.parents.append(context.host)
                    context.host = vessel

                    toreturn.append({"text": f"You entered the {context.host}.", "saycontext": True})
                else:
                    toreturn.append("You do not see the target vessel.")
            case "leave":
                if context.parents:
                    oldname = context.host.name
                    context.host = context.parents.pop()

                    toreturn.append({"text": f"You left the {oldname}.", "saycontext": True})
                else:
                    toreturn.append("You cannot leave a paradox.")
            case "become":
                vessel, index = getVessel(context.host.children, arg)

                if vessel:
                    oldvessel = context.vessel
                    context.vessel = vessel
                    context.host.children.pop(index)
                    context.host.children.append(oldvessel)
                    toreturn.append(f"You became the {vessel}.")
                else:
                    toreturn.append("You do not see the target vessel.")

            case "take":
                vessel, index = getVessel(context.host.children, arg)

                if vessel:
                    context.vessel.inventory.append(vessel)
                    context.host.children.pop(index)
                    toreturn.append(f"You took the {vessel}.")
                else:
                    toreturn.append("You do not see the target vessel.")
            case "drop":
                vessel, index = getVessel(context.vessel.inventory, arg)

                if vessel:
                    context.host.children.append(vessel)
                    context.vessel.inventory.pop(index)
                    toreturn.append(f"You dropped the {vessel}.")
                else:
                    toreturn.append("You do not see the target vessel.")
            case "warp":
                def parentsSearch(parents, name):
                    for p in parents:
                        for i, c in enumerate(p.children):
                            if c.name == name:
                                return c
                        if p.name == name:
                            return p
                    return None 
                    
                vessel = parentsSearch(context.parents, arg)

                if vessel:
                    context.parents.append(context.host)
                    context.host = vessel
                    toreturn.append({"text": f"You warped into the {vessel}.", "saycontext": True})
                else:
                    vessel = getVessel(context.host.children, arg)[0]

                    if vessel:
                        context.parents.append(context.host)
                        context.host = vessel
                        toreturn.append({"text": f"You warped into the {vessel}.", "saycontext": True})
                    else:
                        toreturn.append("You do not see the target vessel.")
            case "note":
                context.host.note = arg
            case "pass":
                context.host.passive = arg
            case "program":
                context.host.program = arg
            case "learn":
                try:
                    toreturn.append(COMMANDS[arg])
                except KeyError:

                    text = "the available commands are: "

                    text += ", ".join(list(COMMANDS.keys())[:-1])

                    text += ", and " + list(COMMANDS.keys())[-1]

                    text += ". to see the documentation for a specific command, use \"learn to move\"."

                    toreturn.append(text)
            case "use":
                vessel, index = getVessel(context.host.children, arg)

                if vessel:
                    toreturn = toreturn + paradiseParser(paradiseTokenizer(vessel.program))
                else:
                    toreturn.append("You do not see the target vessel.")
            case "transform": # FIX
                if arg:
                    ok = True

                    if len(context.parents) == 0:
                        for u in universes:
                            if u.host.name == arg:
                                toreturn.append(f"You cannot make another universe {arg}.")
                                ok = False
                                break

                    if ok: 
                        context.vessel.name = arg
                        toreturn.append(f"You transformed into a {arg}.")
                else:
                    toreturn.append("You cannot transform into nothing.")
            case "move":
                origvessel, oindex = getVessel(context.host.children, arg)

                if origvessel:
                    try:
                        intovessel, index = getVessel(context.host.children, cmdblock[2])

                        if intovessel:
                            intovessel.children.append(context.host.children.pop(oindex))

                            toreturn.append(f"You moved the {origvessel} into {intovessel}.")
                        else:
                            toreturn.append(f"Missing {intovessel}.")
                    except IndexError:
                        toreturn.append(f"Move {origvessel} into what?")
                else:
                    toreturn.append(f"Missing {origvessel}.")

            case "destroy":
                vessel, index = getVessel(context.host.children, arg)

                if vessel:
                    context.host.children.pop(index)
                    toreturn.append(f"You destroyed the {vessel}.")
                else:
                    toreturn.append("You do not see the target vessel.")
            case "observe":
                toreturn.append({"saycontext": True})
            case "universe":
                ok = False

                for i, u in enumerate(universes):
                    if u.host.name == arg:
                        context = universes[i]
                        ok = True
                        toreturn.append({"text": f"You warped into universe {context.host.name}.", "saycontext": True})
                        break

                if not ok:
                    universes.append(Context(arg))
                    context = universes[-1]
                    toreturn.append({"text": f"You created and warped into universe {context.host.name}.", "saycontext": True})


            case "heatdeath":
                ok = False

                for i, u in enumerate(universes):
                    if u.host.name == arg:
                        if u.host.name == context.host.name:
                            toreturn.append("You cannot cause the heat death of your current universe.")
                            ok = True
                            break
                        else:
                            old = universes.pop(i)
                            toreturn.append(f"You caused the heat death of universe {old.host.name}.")
                            ok = True
                            break

                if not ok:
                    toreturn.append(f"You do not see the universe {arg}.")
            case "multiverse":

                metas = []

                for u in universes:
                    currentText = ""

                    if u.host.name == context.host.name:
                        currentText = "*"

                    metas.append(f"      > {u.host.name}{currentText} ({u.host.note})")

                toreturn.append("You see universes:\n" + "\n".join(metas))
            case "import":
                with open(arg, "r") as f:
                    context.imprt(json.loads(f.read()))

                toreturn.append({"text": f"You imported universe {context.host.name}", "saycontext": True})
            case "export":
                with open(context.host.name + ".json", "w+") as f:
                    f.write(json.dumps(context.export()))

                toreturn.append(f"You exported universe {context.host.name}")
            case _:
                pass

    return toreturn
def paradise():
    global displaytext, meta, context

    os.system("clear")    

    while True:
        canSayContext = type(meta) is dict and getValueFromKey(meta, "saycontext")

        if canSayContext:
            print(f"you are a {context.vessel.name}, in the {context.host.name}.\n")

            if context.host.note:
                print(context.host.note + "\n")

            if context.host.children:
                for v in context.host.children:
                    print(f"   - enter the {v}")
                print()

        if displaytext:
            print(displaytext + "\n")

        if canSayContext:
            if context.vessel.inventory:
                for i in context.vessel.inventory:
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
