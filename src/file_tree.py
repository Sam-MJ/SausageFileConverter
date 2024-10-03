from pathlib import Path
from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox


class TreeItem:
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return 1

    def data(self):
        return self.itemData

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, data: list, root_parent_path: Path, parent=None):
        super(TreeModel, self).__init__(parent)

        self.rootItem = TreeItem(parent)
        self.setupModelData(data, root_parent_path, self.rootItem)

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        """If TreeView wants display data, give the path.name, User role returns the full path."""
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            return index.internalPointer().data().name

        if role == Qt.ItemDataRole.UserRole:
            return index.internalPointer().data()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsUserCheckable
        )

    def headerData(self, section, orientation, role):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return str(self.rootItem.itemData)  # self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setupModelData(
        self, list_of_files: list, root_parent_path: Path, root_parent_item: TreeItem
    ):

        parent_dict = {root_parent_path: root_parent_item}

        def has_parent_in_list(
            file_path: Path,
        ):  # can probably be done with recurrsion but this is a bit clearer to understand.
            stack = []
            i = 0
            # if file's parent folder is in is already in the tree, add it as a child.
            """
            root/folder1/folder2/folder3/file.txt
            ^^^^^^^^^^^^^^^^^^^^^^^^
            """
            if file_path.parents[0] in parent_dict.keys():
                # fetch parent item
                parent_item = parent_dict[file_path.parents[0]]
                # create new item for file
                parent_dict[file_path] = TreeItem(file_path, parent_item)
                # add as child to parent item
                parent_item.childItems.append(parent_dict[file_path])

                return

            # if not, go up the folder tree, adding folders that don't exist to the stack.
            """
            root/folder1/folder2/folder3/file.txt
            ^^^^^^^^^^^^^^^^
            stack += root/folder1/folder2

            root/folder1/folder2
            ^^^^^^^^^
            stack += root/folder1
            """
            while True:

                if file_path.parents[i] not in parent_dict.keys():
                    stack.append(file_path.parents[i])
                    i += 1
                else:
                    break

            while len(stack) > 0:
                # take folder out of the stack, starting at the left most
                """
                root/folder1
                """
                new_folder_path = stack.pop()

                # fetch the parent of the new folder and attach it as a child node.
                parent_item = parent_dict[new_folder_path.parent]
                # create new folder node
                new_folder_node = TreeItem(new_folder_path, parent_item)
                # add new folder as child to parent
                parent_item.childItems.append(new_folder_node)
                # add it to the parent dictionary
                parent_dict[new_folder_path] = new_folder_node

            # finally, add file.
            parent_item = parent_dict[file_path.parents[0]]
            parent_dict[file_path] = TreeItem(file_path, parent_item)
            parent_item.childItems.append(parent_dict[file_path])

        for file in list_of_files:
            has_parent_in_list(file)

        # return parent_dict


class FilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(FilterProxyModel, self).__init__(parent)
        self.filter_text_list = []

    def setFilterText(self, text: str):
        """duplicate of def exclusion_str_to_list() in mainwindow"""
        self.filter_text_list = text.split(",")
        temp = []
        # trailing , causes split to an empty list, so remove it.
        for item in self.filter_text_list:
            stripped_item = item.strip()
            if stripped_item == "":
                continue
            temp.append(stripped_item)

        self.filter_text_list = temp
        # updates model when parameters have changed
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        """duplicate of remove_files_with_exclude"""
        if not self.filter_text_list:
            return True
        index = self.sourceModel().index(source_row, 0, source_parent)

        # row has to have none of the keywords in it, if any are, return false.
        accepted = []
        for filter_text in self.filter_text_list:
            if filter_text in self.sourceModel().data(index, 0):
                accepted.append(True)

        return not any(accepted)
