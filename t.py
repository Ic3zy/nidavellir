from nidac import Nidac

a = None
with open("./a.nida", "r") as f:
    a = f.read()


# nida = Nidac(source=a)
nida = Nidac(file_path="./a.nida")
nida.compile()
