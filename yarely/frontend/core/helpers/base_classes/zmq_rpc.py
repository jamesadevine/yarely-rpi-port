# Standard library imports
from xml.etree import ElementTree


class ZMQRPCError(Exception):
    """Base class for ZMQ RPC errors."""
    def __init__(self, msg):
        MSG_PREFIX = 'Invalid RPC XML: '
        super().__init__(MSG_PREFIX + msg)


class ZMQRPC:
    """Provides some common ZMQ RPC operations."""

    def _encapsulate_reply(self, children):
        """Wrap the specified child XML elements in a reply element."""
        if hasattr(self, 'params') and 'token' in self.params:
            root = ElementTree.Element(
                tag='reply', attrib={'token': self.token}
            )
        else:
            root = ElementTree.Element(tag='reply')
        if isinstance(children, ElementTree.Element):
            root.append(children)
        else:
            root.extend(children)
        return root

    def _encapsulate_request(self, children):
        """Wrap the specified child XML elements in a request element."""
        if hasattr(self, 'params') and 'token' in self.params:
            root = ElementTree.Element(
                tag='request', attrib={'token': self.token}
            )
        else:
            root = ElementTree.Element(tag='request')
        if isinstance(children, ElementTree.Element):
            root.append(children)
        else:
            root.extend(children)
        return root

    def _generate_error(self, msg=None):
        """Generate an XML error element (with the given message if
        specified).

        """
        if msg:
            error_root = ElementTree.Element(tag='error',
                                             attrib={'message': msg})
        else:
            error_root = ElementTree.Element(tag='error')
        return error_root

    def _generate_ping(self):
        """Generate an XML ping element."""
        return ElementTree.Element(tag='ping')

    def _generate_pong(self):
        """Generate an XML pong element."""
        return ElementTree.Element(tag='pong')

    def _handle_request_ping(self, msg_root, msg_elem):
        """Handle a ping request."""
        return self._encapsulate_reply(self._generate_pong())

    def _handle_zmq_msg(self, msg):
        """Handle a message received over ZMQ."""
        emsg = ("Received message of type '{msg_type}', no callable found.")

        # Everything received over ZMQ should be XML
        root = ElementTree.XML(msg)

        # Special case - registration
        if root.tag == 'register':
            fn = getattr(self, '_handle_register', None)
            if fn and callable(fn):
                return fn(root)
            else:
                raise ZMQRPCError(emsg.format(msg_type='register'))

        # Everything else (i.e request/reply)
        for elem in root:
            fn_name = '_handle_{root}_{elem}'.format(root=root.tag,
                                                     elem=elem.tag)
            fn = getattr(self, fn_name, None)
            if fn and callable(fn):
                return fn(root, elem)
            else:
                msg_type = '{rt}->{elem}'.format(rt=root.tag, elem=elem.tag)
                raise ZMQRPCError(emsg.format(msg_type=msg_type))
