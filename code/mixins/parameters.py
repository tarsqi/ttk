
class ParameterMixin:

    """Mixin class that provides access to elements in the parameter dictionary that lives on
    Tarsqi and TarsqiDocument instances. This is where parameter defaults are specified."""

    def getopt(self, option_name):
        """Return the option, use None as default."""
        return self.parameters.get(option_name, None)
        
    def getopt_genre(self):
        """Return the 'genre' user option. The default is None."""
        return self.parameters.get('genre', None)
        
    def getopt_platform(self):
        """Return the 'platform' user option. The default is None."""
        return self.parameters.get('platform', None)
        
    def getopt_trap_errors(self):
        """Return the 'trap_errors' user option. The default is False."""
        return self.parameters.get('trap_errors', False)

    def getopt_content_tag(self):
        """Return the 'content_tag' user option. The default is None."""
        return self.parameters.get('content_tag', None)

    def getopt_pipeline(self):
        """Return the 'pipeline' user option. The default is None."""
        return self.parameters.get('pipeline', None)

    def getopt_extension(self):
        """Return the 'extension' user option. The default is ''."""
        return self.parameters.get('extension', '')

    def getopt_remove_tags(self):
        """Return the 'remove_tags' user option. The default is True."""
        return self.parameters.get('remove_tags', True)

    def getopt_perl(self):
        """Return the 'perl' user option. The default is 'perl'."""
        return self.parameters.get('perl', 'perl')
