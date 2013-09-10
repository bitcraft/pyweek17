class Context(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.__dict__.update(kwargs)

    def __enter__(self):
        self.enter()

    def __exit__(self):
        try:
            function = self.callback
        except AttributeError:
            pass
        else:
            function()

        self.exit()

    def init(self, *args, **kwargs):
        pass

    def enter(self):
        pass

    def exit(self):
        pass

    def done(self):
        self.parent.remove(self)

    def fail(self):
        self.parent.remove(self, exit=False)


class ContextDriver(object):
    def __init__(self):
        self._stack = []

    def remove(self, context, exit=True):
        old_context = self.current_context
        self._stack.remove(context)
        if exit:
            context.__exit__()
        if context is old_context:
            new_context = self.current_context
            if new_context:
                new_context.__enter__()

    def queue(self, new_context):
        new_context.parent = self
        new_context.init()
        self._stack.insert(-1, new_context)

    def append(self, new_context, start=True):
        old_context = self.current_context
        new_context.parent = self
        new_context.init()
        self._stack.append(new_context)
        if start:
            if old_context:
                old_context.__exit__()
            new_context.__enter__()

    @property
    def current_context(self):
        try:
            return self._stack[-1]
        except IndexError:
            return None
