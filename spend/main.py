import cmd, sys

class SpendShell(cmd.Cmd):
    intro = "Welcome to spend your hard-earned money.  Type help or ? to list commands.\n"
    prompt = "(spend) "

    def do_quit(self, arg):
        'Stop spending, and exit.'
        return True

if __name__ == '__main__':
    SpendShell().cmdloop()
