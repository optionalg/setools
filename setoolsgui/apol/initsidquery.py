# Copyright 2016, Tresys Technology, LLC
#
# This file is part of SETools.
#
# SETools is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 2.1 of
# the License, or (at your option) any later version.
#
# SETools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with SETools.  If not, see
# <http://www.gnu.org/licenses/>.
#

import logging

from PyQt5.QtCore import Qt, QSortFilterProxyModel, QStringListModel, QThread
from PyQt5.QtGui import QPalette, QTextCursor
from PyQt5.QtWidgets import QCompleter, QHeaderView, QMessageBox, QProgressDialog, QScrollArea
from setools import InitialSIDQuery

from ..logtosignal import LogHandlerToSignal
from ..initsidmodel import InitialSIDTableModel
from ..widget import SEToolsWidget
from .queryupdater import QueryResultsUpdater
from .workspace import load_checkboxes, load_lineedits, load_textedits, \
                       save_checkboxes, save_lineedits, save_textedits


class InitialSIDQueryTab(SEToolsWidget, QScrollArea):

    """An initial SID query."""

    def __init__(self, parent, policy, perm_map):
        super(InitialSIDQueryTab, self).__init__(parent)
        self.log = logging.getLogger(__name__)
        self.policy = policy
        self.query = InitialSIDQuery(policy)
        self.setupUi()

    def __del__(self):
        self.thread.quit()
        self.thread.wait(5000)
        logging.getLogger("setools.initsidquery").removeHandler(self.handler)

    def setupUi(self):
        self.load_ui("initsidquery.ui")

        # set up user autocompletion
        user_completion_list = [str(u) for u in self.policy.users()]
        user_completer_model = QStringListModel(self)
        user_completer_model.setStringList(sorted(user_completion_list))
        self.user_completion = QCompleter()
        self.user_completion.setModel(user_completer_model)
        self.user.setCompleter(self.user_completion)

        # set up role autocompletion
        role_completion_list = [str(r) for r in self.policy.roles()]
        role_completer_model = QStringListModel(self)
        role_completer_model.setStringList(sorted(role_completion_list))
        self.role_completion = QCompleter()
        self.role_completion.setModel(role_completer_model)
        self.role.setCompleter(self.role_completion)

        # set up type autocompletion
        type_completion_list = [str(t) for t in self.policy.types()]
        type_completer_model = QStringListModel(self)
        type_completer_model.setStringList(sorted(type_completion_list))
        self.type_completion = QCompleter()
        self.type_completion.setModel(type_completer_model)
        self.type_.setCompleter(self.type_completion)

        # setup indications of errors on source/target/default
        self.orig_palette = self.type_.palette()
        self.error_palette = self.type_.palette()
        self.error_palette.setColor(QPalette.Base, Qt.red)
        self.clear_name_error()
        self.clear_user_error()
        self.clear_type_error()
        self.clear_role_error()
        self.clear_range_error()

        # set up results
        self.table_results_model = InitialSIDTableModel(self)
        self.sort_proxy = QSortFilterProxyModel(self)
        self.sort_proxy.setSourceModel(self.table_results_model)
        self.table_results.setModel(self.sort_proxy)
        self.table_results.sortByColumn(0, Qt.AscendingOrder)

        # set up processing thread
        self.thread = QThread()
        self.worker = QueryResultsUpdater(self.query, self.table_results_model)
        self.worker.moveToThread(self.thread)
        self.worker.raw_line.connect(self.raw_results.appendPlainText)
        self.worker.finished.connect(self.update_complete)
        self.worker.finished.connect(self.thread.quit)
        self.thread.started.connect(self.worker.update)

        # create a "busy, please wait" dialog
        self.busy = QProgressDialog(self)
        self.busy.setModal(True)
        self.busy.setRange(0, 0)
        self.busy.setMinimumDuration(0)
        self.busy.canceled.connect(self.thread.requestInterruption)
        self.busy.reset()

        # update busy dialog from query INFO logs
        self.handler = LogHandlerToSignal()
        self.handler.message.connect(self.busy.setLabelText)
        logging.getLogger("setools.initsidquery").addHandler(self.handler)

        # Ensure settings are consistent with the initial .ui state
        self.set_name_regex(self.name_regex.isChecked())
        self.criteria_frame.setHidden(not self.criteria_expander.isChecked())
        self.notes.setHidden(not self.notes_expander.isChecked())

        # Range criteria is available only if policy is MLS
        if not self.policy.mls:
            self.range_criteria.setEnabled(False)
            self.range_criteria.setToolTip("MLS is disabled in this policy.")
            self.range_.setToolTip("MLS is disabled in this policy.")
            self.range_exact.setToolTip("MLS is disabled in this policy.")
            self.range_overlap.setToolTip("MLS is disabled in this policy.")
            self.range_subset.setToolTip("MLS is disabled in this policy.")
            self.range_superset.setToolTip("MLS is disabled in this policy.")

        # connect signals
        self.buttonBox.clicked.connect(self.run)
        self.name.textEdited.connect(self.clear_name_error)
        self.name.editingFinished.connect(self.set_name)
        self.name_regex.toggled.connect(self.set_name_regex)
        self.user.textEdited.connect(self.clear_user_error)
        self.user.editingFinished.connect(self.set_user)
        self.user_regex.toggled.connect(self.set_user_regex)
        self.role.textEdited.connect(self.clear_role_error)
        self.role.editingFinished.connect(self.set_role)
        self.role_regex.toggled.connect(self.set_role_regex)
        self.type_.textEdited.connect(self.clear_type_error)
        self.type_.editingFinished.connect(self.set_type)
        self.type_regex.toggled.connect(self.set_type_regex)
        self.range_.textEdited.connect(self.clear_range_error)
        self.range_.editingFinished.connect(self.set_range)

    #
    # Name criteria
    #
    def clear_name_error(self):
        self.name.setToolTip("Match the name.")
        self.name.setPalette(self.orig_palette)

    def set_name(self):
        try:
            self.query.name = self.name.text()
        except Exception as ex:
            self.log.error("Name error: {0}".format(ex))
            self.name.setToolTip("Error: " + str(ex))
            self.name.setPalette(self.error_palette)

    def set_name_regex(self, state):
        self.log.debug("Setting name_regex {0}".format(state))
        self.query.name_regex = state
        self.clear_name_error()
        self.set_name()

    #
    # User criteria
    #
    def clear_user_error(self):
        self.user.setToolTip("Match the user of the context.")
        self.user.setPalette(self.orig_palette)

    def set_user(self):
        try:
            self.query.user = self.user.text()
        except Exception as ex:
            self.log.error("Context user error: {0}".format(ex))
            self.user.setToolTip("Error: " + str(ex))
            self.user.setPalette(self.error_palette)

    def set_user_regex(self, state):
        self.log.debug("Setting user_regex {0}".format(state))
        self.query.user_regex = state
        self.clear_user_error()
        self.set_user()

    #
    # Role criteria
    #
    def clear_role_error(self):
        self.role.setToolTip("Match the role of the context.")
        self.role.setPalette(self.orig_palette)

    def set_role(self):
        try:
            self.query.role = self.role.text()
        except Exception as ex:
            self.log.error("Context role error: {0}".format(ex))
            self.role.setToolTip("Error: " + str(ex))
            self.role.setPalette(self.error_palette)

    def set_role_regex(self, state):
        self.log.debug("Setting role_regex {0}".format(state))
        self.query.role_regex = state
        self.clear_role_error()
        self.set_role()

    #
    # Type criteria
    #
    def clear_type_error(self):
        self.type_.setToolTip("Match the type of the context.")
        self.type_.setPalette(self.orig_palette)

    def set_type(self):
        try:
            self.query.type_ = self.type_.text()
        except Exception as ex:
            self.log.error("Context type error: {0}".format(ex))
            self.type_.setToolTip("Error: " + str(ex))
            self.type_.setPalette(self.error_palette)

    def set_type_regex(self, state):
        self.log.debug("Setting type_regex {0}".format(state))
        self.query.type_regex = state
        self.clear_type_error()
        self.set_type()

    #
    # Range criteria
    #
    def clear_range_error(self):
        self.range_.setToolTip("Match the range of the context.")
        self.range_.setPalette(self.orig_palette)

    def set_range(self):
        try:
            self.query.range_ = self.range_.text()
        except Exception as ex:
            self.log.info("Context range error: " + str(ex))
            self.range_.setToolTip("Error: " + str(ex))
            self.range_.setPalette(self.error_palette)

    #
    # Save/Load tab
    #
    def save(self):
        """Return a dictionary of settings."""
        settings = {}
        save_checkboxes(self, settings, ["criteria_expander", "notes_expander", "name_regex",
                                         "user_regex", "role_regex", "type_regex", "range_exact",
                                         "range_overlap", "range_subset", "range_superset"])
        save_lineedits(self, settings, ["name", "user", "role", "type_", "range_"])
        save_textedits(self, settings, ["notes"])
        return settings

    def load(self, settings):
        load_checkboxes(self, settings, ["criteria_expander", "notes_expander", "name_regex",
                                         "user_regex", "role_regex", "type_regex", "range_exact",
                                         "range_overlap", "range_subset", "range_superset"])
        load_lineedits(self, settings, ["name", "user", "role", "type_", "range_"])
        load_textedits(self, settings, ["notes"])

    #
    # Results runner
    #
    def run(self, button):
        # right now there is only one button.
        self.query.range_overlap = self.range_overlap.isChecked()
        self.query.range_subset = self.range_subset.isChecked()
        self.query.range_superset = self.range_superset.isChecked()

        # start processing
        self.busy.setLabelText("Processing query...")
        self.busy.show()
        self.raw_results.clear()
        self.thread.start()

    def update_complete(self, count):
        self.log.info("{0} initial SID statment(s) found.".format(count))

        # update sizes/location of result displays
        if not self.busy.wasCanceled():
            self.busy.setLabelText("Resizing the result table's columns; GUI may be unresponsive")
            self.busy.repaint()
            self.table_results.resizeColumnsToContents()

        if not self.busy.wasCanceled():
            self.busy.setLabelText("Resizing the result table's rows; GUI may be unresponsive")
            self.busy.repaint()
            self.table_results.resizeRowsToContents()

        if not self.busy.wasCanceled():
            self.busy.setLabelText("Moving the raw result to top; GUI may be unresponsive")
            self.busy.repaint()
            self.raw_results.moveCursor(QTextCursor.Start)

        self.busy.reset()
