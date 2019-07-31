from tkinter import ttk
from tkinter import EventType
from typing import Dict
from typing import Any

from ue import UEBase


class Tree(ttk.Treeview):
    def __init__(self, frame, columns=('type', 'value'), **kw):
        super().__init__(frame, columns=columns, **kw)
        self.grid(column=0, row=0, sticky='nsew')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.column('#0', stretch=0)
        self.heading('type', text='Type')
        self.heading('value', text='Value')
        self.column('type', width=110, stretch=False, anchor='e')
        self.column('value', anchor='w')

        # Styles for some different types
        # https://lospec.com/palette-list/island-joy-16
        self.tag_configure('int', foreground='#cb4d68')
        self.tag_configure('bool', foreground='#393457')
        self.tag_configure('Guid', foreground='#1e8875')
        self.tag_configure('NameIndex', foreground='#11adc1')
        self.tag_configure('StringProperty', foreground='#11adc1')
        self.tag_configure('Property', foreground='#393457')

        # Support virtual tree items with the 'placeholdered' tag
        self.tag_bind('placeholdered', '<<TreeviewOpen>>', self.on_tree_open)

        # Scroll bar to control the treeview
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.yview)
        vsb.grid(row=0, column=1, sticky='nse')
        self.configure(yscrollcommand=vsb.set)

        self.treenodes: Dict[str, Any] = {}
        self.LEAF_TYPES = (
    'str',
    'StringProperty',
    'Guid',
)

    def on_tree_open(self, evt: EventType):
        assert self

        # This is called when a node containing a placeholder is opened for the first time
        item_id = self.selection()[0]
        node = self.treenodes[item_id]

        # Remove the placeholder item under this item
        self.delete(item_id + '_placeholder')

        # Remove placeholdered tag
        tags = self.item(item_id)['tags']
        tags.remove('placeholdered')
        self.item(item_id, tags=tags)

        # Convert and insert the proper nodes
        self.insert_fields_for_node(item_id)

    @staticmethod
    def node_id(node, parent_id=None):
        """Create a string ID for a node."""
        if isinstance(node, UEBase):
            new_id = str(id(node))
            if parent_id:
                return parent_id + '_' + new_id
            return new_id
        return None

    @staticmethod
    def type_name(value):
        """Return the type of a value as a string."""
        return str(type(value).__name__)

    def has_children(self, value):
        value_type = self.type_name(value)
        if value_type in self.LEAF_TYPES:
            return False
        if isinstance(value, UEBase) or type(value) == list:  # isinstance(value, Iterable)
            return True
        return False

    @staticmethod
    def get_node_iterator(node):
        if isinstance(node, list):
            return ((f'0x{i:X} ({i})', value) for i, value in enumerate(node))
        if isinstance(node, UEBase):
            return ((name, node.field_values[name]) for name in
                    getattr(node, 'field_order', None) or node.field_values.keys())
        raise TypeError("Invalid node type for iterator")

    def add_placeholder_node(self, item_id):
        # Add a tag to specifiy this node as having a placeholder (so it will raise an event when opened)
        tags = self.item(item_id)['tags']
        if not hasattr(tags, 'append'):
            tags = [tags]
        tags.append('placeholdered')
        self.item(item_id, tags=tags)

        # Add a dummy node to it so it look slike it can be opened
        placeholder_id = self.insert(item_id, 'end', item_id + '_placeholder', text='<virtual tree placeholder>')

    def add_asset_to_root(self, asset):
        item_id = self.insert('', 'end', self.node_id(asset), text=asset.name, values=(self.type_name(asset),))
        self.treenodes[item_id] = asset
        self.add_placeholder_node(item_id)

    @staticmethod
    def get_value_as_string(value):
        if isinstance(value, list):
            return f'{len(value)} entries'
        if isinstance(value, type):
            return value.__name__
        return str(value)

    def insert_fields_for_node(self, parent_id):
        node = self.treenodes[parent_id]
        skip_level_name = getattr(node, 'skip_level_field', None)
        if skip_level_name:
            node = node.field_values.get(skip_level_name, node)
        fields = self.get_node_iterator(node)
        for name, value in fields:
            type_name = str(type(value).__name__)
            new_id = self.node_id(value, parent_id)
            str_value = self.get_value_as_string(value)
            item_id = self.insert(parent_id, 'end', new_id, text=name, values=(type_name, str_value), tags=(type_name,))
            if self.has_children(value):
                self.treenodes[item_id] = value
                self.add_placeholder_node(item_id)
