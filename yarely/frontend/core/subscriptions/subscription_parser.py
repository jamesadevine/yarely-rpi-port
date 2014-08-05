# Standard library imports
from xml.etree import ElementTree
from urllib.error import URLError
from urllib.request import urlopen

# Local (Yarely) imports
from yarely.frontend.core.helpers.base_classes.constraint import \
        ConstraintConditionMatchError, ConstraintNotImplementedError, \
        ConstraintsParser, PriorityConstraint, PriorityConstraintCondition


class XMLSubscriptionParserError(Exception):
    """Base class for subscription parsing errors."""
    pass


class XMLSubscriptionParser:
    """Parses subscription-update XML (as an etree) into a
    Content Descriptor Set object.

    """
    def __init__(self, etree_elem):
        content_set_elem = etree_elem.find('content-set')
        if content_set_elem is None:
            msg = "Expected element 'content-set' not found.\n"
            msg += "XML source is:\n{}"
            xml_src = ElementTree.tostring(etree_elem).decode()
            raise XMLSubscriptionParserError(msg.format(xml_src))
        self.etree = ElementTree.ElementTree(content_set_elem)
        self.root_cds = ContentDescriptorSet(self.etree.getroot())
        root_file_element = ElementTree.Element('requires-file')
        sources_element = ElementTree.Element('sources')
        root_file_element.append(sources_element)
        uri_element = ElementTree.Element('uri')
        uri_element.text = etree_elem.attrib['uri']
        sources_element.append(uri_element)
        root_source = SubscriptionElementFile(root_file_element)
        self.root_cds.add_file(root_source)

    def get_descriptor_set(self):
        """Gets the Content Descriptor Set generated as a result of parsing."""
        return self.root_cds


#
# Below: representing the physical files containing content
# descriptor sets and content items.
#
class SubscriptionElementFile:
    """A File object (sources plus hashes) for Subscription
    items (Content Descriptor Sets and Content Items).

    Sample XML input (passed in as an etree Element):

        <requires-file>
            <hashes>
                <hash type='md5'>eb8c567e9ac78e9ea58c0ac45385c10b</hash>
            </hashes>
            <sources>
                <uri>http://tinyurl.com/award.jpg</uri>
            </sources>
        </requires-file>

    """
    def __init__(self, etree_elem):
        super().__init__()
        self.etree = ElementTree.ElementTree(etree_elem)
        # Handle sources
        self._sources = []
        sources_elem = etree_elem.find('sources')
        if sources_elem is None or not len(sources_elem):
            msg = ('Remote items must have a sources tag'
                   ' containing at least one source.')
            raise XMLSubscriptionParserError(msg)
        for elem in sources_elem:
            self._sources.append(SubscriptionElementFileSource(elem))

        # Handle hashes (optional)
        self._hashes = list()
        hashes_elem = etree_elem.find('hashes')
        if hashes_elem is not None:
            hash_types = dict()
            for elem in hashes_elem:
                # Create a new Hash object
                hash = SubscriptionElementFileHash(elem)

                # Check for duplicates - one file should not have two
                # different hashes of the same type
                if hash.get_type() in hash_types:
                    if hash_types[hash.get_type()] != hash.get_hash():
                        self._hashes = [elem for elem in self._hashes
                                        if elem.get_type() != hash.get_type()]

                # Not a duplicate - associate the new Hash object with
                # this File
                else:
                    hash_types[hash.get_type()] = hash.get_hash()
                    self._hashes.append(hash)

    def __getattr__(self, name):
        try:
            (get, hash_type, hash) = name.split('_')
            if get == 'get' and hash == 'hash':
                for hash_obj in self._hashes:
                    if hash_obj.get_type() == hash_type.lower():
                        return hash_obj.get_hash
        except:
            pass
        raise NameError('Name \'{name}\' is not defined'.format(name=name))

    def get_sources(self):
        """Get the list of sources for this file."""
        return self._sources

    def get_identity(self):
        """Return an identity string suitable for comparison, a
           hash is preferred, a URI also works as a fallback to
           non-hashable typed things."""

        try:
            return self.get_md5_hash()
        except NameError:
            pass

        try:
            return self.get_sha1_hash()
        except NameError:
            pass

        try:
            return self.get_sources()[0].get_uri()
        except:
            return self

#
# Below: representing the different hashes for the physical
# files containing content descriptor sets and content items.
#


class SubscriptionElementFileHash:
    """A File hash object.

    Sample XML input (passed in as an etree Element):

        <hash type='md5'>eb8c567e9ac78e9ea58c0ac45385c10b</hash>

    """
    def __init__(self, etree_elem):
        super().__init__()
        self.etree = ElementTree.ElementTree(etree_elem)
        self.attrib = self.etree.getroot().attrib.copy()
        try:
            self._type = self.attrib.pop('type').lower()
        except KeyError as e:
            msg = "Tag 'hash' must contain 'type' attribute, not found."
            raise XMLSubscriptionParserError(msg) from e
        self._hash = self.etree.getroot().text.strip()
        if not self.get_hash():
            msg = "Tag 'hash' must contain text element, not found."
            raise XMLSubscriptionParserError(msg) from e

    def get_type(self):
        """Get a string for describing the type of this hash (e.g. 'md5')."""
        return self._type

    def get_hash(self):
        """Get the hash value for this object."""
        return self._hash

#
# Below: representing the different methods for retrieving the physical
# files containing content descriptor sets and content items.
#


class SubscriptionElementFileSource:
    """A Source (URI plus optional data such as refresh rate) for
    Subscription items (Content Descriptor Sets and Content Items).

    Sample XML input (passed in as an etree Element):

        <uri>http://tinyurl.com/award.jpg</uri>

    """
    def __init__(self, etree_elem):
        super().__init__()
        self.etree = ElementTree.ElementTree(etree_elem)
        root = self.etree.getroot()
        self.attrib = root.attrib.copy()

        # compulsory text
        self._uri = root.text.strip()
        if not self.get_uri():
            msg = "Tag 'uri' must contain text element, not found."
            raise XMLSubscriptionParserError(msg)

        # optional attributes (see also __getattr__)
        try:
            self.refresh = self.attrib.pop('refresh')
        except KeyError:
            self.refresh = None

    def __getattr__(self, name):
        if hasattr(self, 'attrib') and name in self.attrib:
            return self.attrib[name]
        else:
            raise NameError('Name \'{name}\' is not defined'.format(name=name))

    def get_uri(self):
        """Get the URI associated with this source."""
        return self._uri


#
# Below: representing a content descriptor set or content item
#
class SubscriptionElement:
    """Base class for Content Descriptor Sets and Content Items.
    Includes common features such as auth, contraints and sources.

    """
    def __init__(self, etree_elem, parent=None):
        super().__init__()
        self.etree = ElementTree.ElementTree(etree_elem)
        #print('SUBSCRIPTIONELEMENT: '+str(ElementTree.tostring(etree_elem)))
        self._parent = parent
        root = self.etree.getroot()

        # Added exception to try to track down where this comes from:
        # self._type = root.attrib.get('type', 'remote')
        # AttributeError: 'NoneType' object has no attribute 'attrib'
        if root is None:
            etree_xml_str = ElementTree.ElementTree.tostring(self.etree).decode()
            msg = 'No root XML found, etree is:\n"{etree}"'
            msg = msg.format(etree=etree_xml_str)
            raise XMLSubscriptionParserError(msg)

        # Default assumption (used mainly by content-items) is
        # that this is a remotely stored element.
        self._type = root.attrib.get('type', 'remote')
        if self.get_type() not in ['inline', 'remote']:
            msg = 'Invalid element type "{type}"'.format(type=self.get_type())
            raise XMLSubscriptionParserError(msg)

        # FIXME - for future implementations
        self.auth = None if self.etree.find('auth') is None else None
        self.feedback = None if self.etree.find('feedback') is None else None

        # Retreive any constraints
        self._constraints = []
        constraints = self.etree.find('constraints')
        if constraints is not None:
            constraint_parser = ConstraintsParser(constraints)
            self._constraints = constraint_parser.get_constraints()

        # Remote items must have at least one requires-file tag
        self._files = []
        if self.get_type() == 'remote':
            required_files = self.etree.findall('requires-file')
            if len(required_files) is 0:
                msg = 'Remote item must contain at least one requires-file tag'
                raise XMLSubscriptionParserError(msg)
            for elem in required_files:
                self.add_file(SubscriptionElementFile(elem))

    def add_file(self, sources_list):
        """Add a file to the list of files for this object."""
        self._files.append(sources_list)

    def constraints_are_met(self, condition=None, ignore_unimplemented=True,
                            recurse_up_tree=True):
        """Check to see if this object's constraints are met in the specified
        condition (defaults to right now).

        The ignore_unimplemented flag is used to accept/reject unimplemented
        constraints.

        """
        # Get all our constraints in one place
        constraints = self.get_constraints(
            recurse_up_tree=recurse_up_tree
        )

        # Look for constraints that are NOT met
        found_applicable_constraint = False
        for constraint in constraints:
            try:
                constraint_met = constraint.is_met(condition)
                found_applicable_constraint = True
                if not constraint_met:
                    return False
            except ConstraintNotImplementedError:
                if not ignore_unimplemented:
                    return False
            # The condition is not applicable to this constraint type
            except ConstraintConditionMatchError:
                pass

        # Some constraints need a default value check to behave correctly
        if not found_applicable_constraint:
            # If we're looking for items at a specific priority then we
            # need to assume items without a PriorityContraint set on them
            # should play at the default priority in order for us to make
            # the comparison.
            if isinstance(condition, PriorityConstraintCondition):
                if condition.data != PriorityConstraint.DEFAULT_VALUE:
                    return False

        # All constraints met
        return True

    def count_files(self):
        """Return the number of files in the list of files for this object."""
        return 0 if self._files is None else len(self._files)

    def get_constraints(self, recurse_up_tree=True,
                        return_as_etree_elem=False):
        """Get the constraints for this object."""
        constraints = []
        constraints.extend(self._constraints)
        if recurse_up_tree and self._parent is not None:
            constraints.extend(
                self._parent.get_constraints(recurse_up_tree=recurse_up_tree)
            )

        if not return_as_etree_elem:
            return constraints
        constraints_elem = ElementTree.Element('constraints')
        constraints_elem.extend([
            constraint.etree.getroot() for constraint in constraints
        ])
        return constraints_elem

    def get_parent(self):
        """Get the parent container for this object."""
        return self._parent

    def get_files(self):
        """Get the list of files for this object."""
        return self._files

    def get_type(self):
        """Get the type (remote/inline) for this object."""
        return self._type

    def get_xml(self):
        """Get a representation of this object as an XML string."""
        return ElementTree.tostring(self.etree.getroot(), encoding="unicode")

    def __str__(self):
        """Get a representation of this object (normally a URI)."""
        try:
            return self.get_files()[0].get_sources()[0].get_uri()
        except IndexError:    # This exception occurs for 'inline' sets/items
            return repr(self)

    def __eq__(self, other):
        if (not isinstance(other, self.__class__)):
            return False

        # Step 1 - Check the file itself
        for file in self.get_files():
            found_this_file = False

            for other_files in other.get_files():
                if file.get_identity() == other_files.get_identity():
                    found_this_file = True
                    break
            if not found_this_file:
                return False

        # Step 2 - Check the constraints applied to the file
        own_cnstrts = self.get_constraints(
            recurse_up_tree=True, return_as_etree_elem=False
        )
        other_cnstrts = other.get_constraints(
            recurse_up_tree=True, return_as_etree_elem=False
        )
        return own_cnstrts == other_cnstrts

    def __ne__(self, other):
        return not self.__eq__(other)


class ContentDescriptorSet(SubscriptionElement):
    """A Content Descriptor Set.

    Sample XML input (passed in as an etree Element):

        <content-set name='mycontentset1' type='inline'>
            <constraints>
                <scheduling-constraints>
                    <playback order='random' avoid-context-switch='false'/>
                    <time><between start='08:30:00' end='23:30:00'/></time>
                </scheduling-constraints>
            </constraints>
            <content-item content-type='image/jpeg' size='1 bytes'>
                <requires-file>
                    <hashes>
                        <hash type='md5'>eb8c567e9ac78e9ea58c0ac45385c10</hash>
                    </hashes>
                    <sources>
                        <uri>http://tinyurl.com/award.jpg</uri>
                    </sources>
                </requires-file>
            </content-item>
        </content-set>

    """
    def __init__(self, etree_elem, parent=None):
        super().__init__(etree_elem, parent)
        if self.get_type() == 'remote' and self.count_files() is not 1:
            msg = ('A remote content set must be composed of exactly one file,'
                   ' found {len}')
            raise XMLSubscriptionParserError(
                msg.format(len=self.count_files())
            )

        self._children = []
        root = self.etree.getroot()
        for elem in root:
            if elem.tag == 'content-set':
                child = ContentDescriptorSet(elem, self)
                self._children.append(child)
            elif elem.tag == 'content-item':
                child = ContentItem(elem, self)
                self._children.append(child)

    def get_children(self):
        """Return the child elements within this content descriptor set
        maintaining their types (i.e. a mix of ContentSets and ContentItems).

        """
        return self._children[:]

    def get_content_items(self, condition=None, ignore_unimplemented=True,
                          flatten=True):
        """Return the child elements within this content descriptor set
        as a list of ContentItems.

        If condition is not None, the child elements constraints must
        match the condition to be included. The ignore_unimplemented flag is
        used to accept/reject unimplemented constraints.

        If flatten is False then the list will contain other lists representing
        child ContentSets e.g.:

            >>> cds.get_children(flatten=False)
            [[ContentItem object at 0x10176f510>],
             [<ContentItem object at 0x10176fa90>]]

        Vs.

            >>> cds.get_children(flatten=True)
            [<ContentItem object at 0x10176f510>,
             <ContentItem object at 0x10176ff90>]

        """
        filtered_children = []
        for child in self.get_children():
            if isinstance(child, ContentItem):
                if (condition is None or child.constraints_are_met(
                    condition, ignore_unimplemented
                )):
                    filtered_children.append(child)
            elif isinstance(child, ContentDescriptorSet):
                if (condition is None or child.constraints_are_met(
                    condition, ignore_unimplemented
                )):
                    items = child.get_content_items(
                        condition, ignore_unimplemented
                    )
                    if len(items):
                        if flatten:
                            filtered_children.extend(items)
                        else:
                            filtered_children.append(items)

        return filtered_children

    def get_inline_xml(self):
        """Return the representation of this descriptor set as an XML
        string but ONLY if the object is not actually a pointer to a
        remote descriptor set. If the descriptor set is a pointer to a
        remote descriptor set return None.

        """
        return self.get_xml() if self.get_type() == 'inline' else None


class ContentItem(SubscriptionElement):
    """A Content Item.

    Sample XML input (passed in as an etree Element):

        <content-item content-type='image/jpeg; charset=binary' size='1 bytes'>
            <requires-file>
                <hashes>
                    <hash type='md5'>eb8c567e9ac78e9ea58c0ac45385c10b</hash>
                </hashes>
                <sources>
                    <uri>http://tinyurl.com/award.jpg</uri>
                </sources>
            </requires-file>
        </content-item>

    """
    def __init__(self, etree_elem, parent=None):
        super().__init__(etree_elem, parent)
        self._content_type = (etree_elem.attrib['content-type']
                              if 'content-type' in etree_elem.attrib else None)

    def get_content_type(self):
        """Return the content (mime) type of this item."""
        if self._content_type is None and self.count_files() is 1:
            sources = self.get_files()[0].get_sources()
            for source in sources:
                try:
                    file_handle = urlopen(source.get_uri())
                    self._content_type = file_handle.info()['Content-Type']
                    break
                except URLError:
                    continue
        return ('unknown/unknown' if self._content_type is None
                                  else self._content_type)
