"""
Context processors for registry app
"""

def validation_error(request):
    """
    Add validation error from session to context
    """
    error = request.session.pop('validation_error', None)
    return {'validation_error': error}
