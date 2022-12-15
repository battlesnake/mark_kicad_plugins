from .choice_box import ChoiceBox


def test():
	print(ChoiceBox("TITLE", "MESSAGE", ["a", "b", "42"], False).execute())
	print(ChoiceBox("TITLE", "MESSAGE", ["a", "b", "42"], True).execute())
