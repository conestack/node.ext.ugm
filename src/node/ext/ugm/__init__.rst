node.ext.ugm
============

``node.ext.ugm`` provides a main hook for ``cone.app`` which initializes the
UGM API implementation contained in ``node.ext.ugm.file`` and set it as
authentication implementation. The created ugm won't work here due to missing
configuration.::

    >>> from node.ext.ugm import initialize_default_ugm
    >>> initialize_default_ugm(None, None, dict())
    <Ugm object 'ugm' at ...>
