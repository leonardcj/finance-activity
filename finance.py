# Copyright 2008 by Wade Brainerd.  
# This file is part of Finance.
#
# Finance is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Finance is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Finance.  If not, see <http://www.gnu.org/licenses/>.
#!/usr/bin/env python
"""Finance - Home financial software for the OLPC XO."""

# Import standard Python modules.
import logging, os, math, time, copy, json, time, datetime
from gettext import gettext as _

# Import PyGTK.
import gobject, pygtk, gtk, pango

import cairo

# Import Sugar UI modules.
import sugar.activity.activity
from sugar.graphics import *

# Initialize logging.
log = logging.getLogger('Finance')
log.setLevel(logging.DEBUG)
logging.basicConfig()

CATEGORY_COLORS = [
    (1.0,1.0,1.0),
    (1.0,1.0,0.6),
    (1.0,1.0,0.8),
    (1.0,0.6,1.0),
    (1.0,0.6,0.6),
    (1.0,0.6,0.8),
    (1.0,0.8,1.0),
    (1.0,0.8,0.6),
    (1.0,0.8,0.8),
    (0.6,1.0,1.0),
    (0.6,1.0,0.6),
    (0.6,1.0,0.8),
    (0.6,0.6,1.0),
    (0.6,0.6,0.6),
    (0.6,0.6,0.8),
    (0.6,0.8,1.0),
    (0.6,0.8,0.6),
    (0.6,0.8,0.8),
    (0.8,1.0,1.0),
    (0.8,1.0,0.6),
    (0.8,1.0,0.8),
    (0.8,0.6,1.0),
    (0.8,0.6,0.6),
    (0.8,0.6,0.8),
    (0.8,0.8,1.0),
    (0.8,0.8,0.6),
    (0.8,0.8,0.8),
]

def get_category_color(catname):
    return CATEGORY_COLORS[catname.__hash__() % len(CATEGORY_COLORS)]

def get_category_color_str(catname):
    color = get_category_color(catname)
    return "#%02x%02x%02x" % (int(color[0]*255), int(color[1]*255), int(color[2]*255))

def prev_month(d):
    if d.month == 1:
        return datetime.date(d.year-1, 12, 1)
    else:
        return datetime.date(d.year, d.month-1, 1)
      
def next_month(d):
    if d.month == 12:
        return datetime.date(d.year+1, 1, 1)
    else:
        return datetime.date(d.year, d.month+1, 1)

class BudgetScreen(gtk.VBox):
    def __init__(self, activity):
        gtk.VBox.__init__(self)

        self.activity = activity

        self.category_total = {}
        self.sorted_categories = []
 
        self.budgetbox = gtk.VBox()

        self.pack_start(self.budgetbox)

    def build(self):
        # Build the category totals.
        self.category_total = {}
        for t in self.activity.visible_transactions:
            cat = t['category']
            amount = t['amount']
            
            if t['type'] == 'debit':
                if not self.category_total.has_key(cat):
                    self.category_total[cat] = amount
                else: 
                    self.category_total[cat] += amount 

        # Generate a list of names sorted by total.
        self.sorted_categories = self.category_total.keys()
        #self.sorted_categories.sort(lamba a, b: cmp(self.category_total[a], self.category_total[b]))

        # Clear and rebuild the labels box.
        for w in self.budgetbox.get_children():
            self.budgetbox.remove(w)

        catgroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        amountgroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        
        for c in self.sorted_categories:
            hbox = gtk.HBox()

            catlabel = gtk.Label()
            catlabel.set_markup(c)
            catgroup.add_widget(catlabel)

            color = get_category_color_str(c)

            ebox = gtk.EventBox()
            ebox.modify_bg(gtk.STATE_NORMAL, ebox.get_colormap().alloc_color(color))
            ebox.add(catlabel)

            amountlabel = gtk.Label()
            amountlabel.set_markup('<b>Spent:</b> %.2f' % self.category_total[c])
            amountgroup.add_widget(amountlabel)

            budgetlabel = gtk.Label()
            budgetlabel.set_markup('<b>Budget:</b> ')

            budgetentry = gtk.Entry()
            budgetentry.set_size_request(120, -1)
            #if self.activity.budget_map.has_key(c):
            #    b = self.activity.budget_map[c]
            #    budgetentry.set_text('%.2f' % c['amount'])

            freqcombo = gtk.combo_box_new_text()
            freqcombo.append_text(_('Daily'))
            freqcombo.append_text(_('Weekly'))
            freqcombo.append_text(_('Monthly'))
            freqcombo.append_text(_('Annually'))
            freqcombo.set_active(2)

            hbox.pack_start(ebox, False, False, 20)
            hbox.pack_start(budgetlabel, False, False)
            hbox.pack_start(budgetentry, False, False)
            hbox.pack_start(freqcombo, False, False)
            hbox.pack_start(amountlabel, False, False, 40)

            self.budgetbox.pack_end(hbox, True, False, 5)

        self.show_all()
            
class ChartScreen(gtk.HBox):
    def __init__(self, activity):
        gtk.HBox.__init__(self)

        self.activity = activity

        self.category_total = {}
        self.sorted_categories = []

        self.area = gtk.DrawingArea()
        self.area.connect('expose-event', self.area_expose_cb)

        label = gtk.Label()
        label.set_markup('<b>'+_('Debit Categories')+'</b>')

        self.catbox = gtk.VBox()

        box = gtk.VBox()
        box.pack_start(gtk.VBox(), False, False, 40)
        box.pack_start(label, False, False)
        box.pack_start(gtk.HSeparator(), False, False)
        box.pack_start(self.catbox, False, False, 10)
        box.pack_start(gtk.VBox(), True, True)
 
        self.pack_start(self.area, True, True)
        self.pack_start(box, False, False, 40)

        self.show_all()
       
        self.build()

    def build(self):
        # Build the category totals.
        self.category_total = {}
        for t in self.activity.visible_transactions:
            cat = t['category']
            amount = t['amount']
            
            if t['type'] == 'debit':
                if not self.category_total.has_key(cat):
                    self.category_total[cat] = amount
                else: 
                    self.category_total[cat] += amount 

        # Generate a list of names sorted by total.
        self.sorted_categories = self.category_total.keys()
        #self.sorted_categories.sort(lamba a, b: cmp(self.category_total[a], self.category_total[b]))

        # Clear and rebuild the labels box.
        for w in self.catbox.get_children():
            self.catbox.remove(w)

        catgroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        amountgroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        
        for c in self.sorted_categories:
            hbox = gtk.HBox()

            catlabel = gtk.Label()
            catlabel.set_markup(c)
            catgroup.add_widget(catlabel)

            color = get_category_color_str(c)

            amountlabel = gtk.Label()
            amountlabel.set_markup('%.2f' % self.category_total[c])
            amountgroup.add_widget(amountlabel)

            hbox.pack_start(amountlabel, True, True, 20)
            hbox.pack_start(catlabel, True, True, 20)

            ebox = gtk.EventBox()
            ebox.modify_bg(gtk.STATE_NORMAL, ebox.get_colormap().alloc_color(color))
            ebox.add(hbox)

            self.catbox.pack_end(ebox, False, False, 5)

        self.show_all()

    def area_expose_cb(self, widget, event):
        context = widget.window.cairo_create()
        context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        context.clip()

        # Draw pie chart.
        bounds = widget.get_allocation()

        x = bounds.width/2
        y = bounds.height/2
        r = min(bounds.width, bounds.height)/2 - 10 

        total = 0
        for c in self.sorted_categories:
            total += self.category_total[c]

        if total != 0:
            angle = 0.0

            for c in self.sorted_categories:
                slice = 2*math.pi * self.category_total[c] / total
                color = get_category_color(c)
 
                context.move_to(x, y)
                context.arc(x, y, r, angle, angle + slice)
                context.close_path()

                context.set_source_rgb(color[0], color[1], color[2])
                context.fill_preserve()

                context.set_source_rgb(0, 0, 0)
                context.stroke()

                angle += slice


class RegisterScreen(gtk.VBox):
    def __init__(self, activity):
        gtk.VBox.__init__(self)

        self.activity = activity

        # Build the transaction list.
        self.treeview = gtk.TreeView()
        self.treeview.set_rules_hint(True)

        # Note that the only thing we store in our liststore is the transaction id,
        # all the actual data is in the activity database.
        self.liststore = gtk.ListStore(gobject.TYPE_INT)
        self.treeview.set_model(self.liststore)

        # Construct the columns.
        renderer = gtk.CellRendererText()
        renderer.props.editable = True
        renderer.connect('edited', self.description_edit_cb)
        col = gtk.TreeViewColumn(_('Description'), renderer)
        col.set_cell_data_func(renderer, self.description_render_cb) 
        col.set_expand(True)
        self.treeview.append_column(col)

        renderer = gtk.CellRendererText()
        renderer.props.editable = True
        renderer.connect('edited', self.amount_edit_cb)
        col = gtk.TreeViewColumn(_('Amount'), renderer)
        col.set_cell_data_func(renderer, self.amount_render_cb) 
        col.set_alignment(0.5)
        col.set_min_width(120)
        self.treeview.append_column(col)

        renderer = gtk.CellRendererText()
        renderer.props.editable = True
        renderer.connect('edited', self.date_edit_cb)
        col = gtk.TreeViewColumn(_('Date'), renderer)
        col.set_alignment(0.5)
        col.set_cell_data_func(renderer, self.date_render_cb) 
        col.set_min_width(150)
        self.treeview.append_column(col)

        renderer = gtk.CellRendererText()
        renderer.props.editable = True
        renderer.connect('edited', self.category_edit_cb)
        col = gtk.TreeViewColumn(_('Category'), renderer)
        col.set_cell_data_func(renderer, self.category_render_cb) 
        col.set_alignment(0.5)
        col.set_min_width(300)
        self.treeview.append_column(col)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.add(self.treeview)

        self.pack_start(scroll, True, True, 0)

        self.build()

    def build(self):
        # Build liststore.
        self.liststore.clear()
        for t in self.activity.visible_transactions:
            self.liststore.append((t['id'],))

    def description_render_cb(self, column, cell_renderer, model, iter):
        id = model.get_value(iter, 0)
        t = self.activity.transaction_map[id]
        cell_renderer.set_property('text', t['name'])

    def description_edit_cb(self, cell_renderer, path, new_text):
        id = self.liststore[path][0]
        t = self.activity.transaction_map[id]
        t['name'] = new_text

    def amount_render_cb(self, column, cell_renderer, model, iter):
        id = model.get_value(iter, 0)
        t = self.activity.transaction_map[id]
        cell_renderer.set_property('xalign', 1.0)
        if t['type'] == 'credit':
            cell_renderer.set_property('foreground', '#4040ff')
            cell_renderer.set_property('text', '%.2f' % t['amount'])
        else:
            cell_renderer.set_property('foreground', '#ff4040')
            cell_renderer.set_property('text', '-%.2f' % t['amount'])

    def amount_edit_cb(self, cell_renderer, path, new_text):
        id = self.liststore[path][0]
        t = self.activity.transaction_map[id]
        amount = float(new_text)
        if amount > 0 and t['type'] == 'debit':
            t['type'] = 'credit'
        if amount < 0 and t['type'] == 'credit':
            t['type'] = 'debit'
        t['amount'] = abs(float(new_text))
        self.activity.update_summary()

    def date_render_cb(self, column, cell_renderer, model, iter):
        id = model.get_value(iter, 0)
        t = self.activity.transaction_map[id]
        when = datetime.date.fromordinal(t['date'])
        cell_renderer.set_property('text', when.isoformat())
        cell_renderer.set_property('xalign', 0.5)

    def date_edit_cb(self, cell_renderer, path, new_text):
        id = self.liststore[path][0]
        t = self.activity.transaction_map[id]
        when = time.strptime(new_text, "%Y-%m-%d")
        when = datetime.date(when[0], when[1], when[2])
        t['date'] = when.toordinal()
        self.activity.build_screen()

    def category_render_cb(self, column, cell_renderer, model, iter):
        id = model.get_value(iter, 0)
        t = self.activity.transaction_map[id]
        cell_renderer.set_property('text', t['category'])
        cell_renderer.set_property('background', get_category_color_str(t['category']))

    def category_edit_cb(self, cell_renderer, path, new_text):
        id = self.liststore[path][0]
        t = self.activity.transaction_map[id]
        t['category'] = new_text

    def newcredit_cb(self, widget):
        id = self.activity.create_transaction(_('New Credit Transaction'), 'credit', 0)
        iter = self.liststore.append((id,))
        # Set cursor and begin editing the description.
        self.treeview.set_cursor(self.liststore.get_path(iter), self.treeview.get_column(0), True)
        
    def newdebit_cb(self, widget):
        id = self.activity.create_transaction(_('New Debit Transaction'), 'debit', 0)
        iter = self.liststore.append((id,))
        # Set cursor and begin editing the description.
        self.treeview.set_cursor(self.liststore.get_path(iter), self.treeview.get_column(0), True)
        
    def eraseitem_cb(self, widget):
        sel = self.treeview.get_selection()
        model, iter = sel.get_selected()
        if iter:
            id = model.get_value(iter, 0)
            self.activity.destroy_transaction(id)
            self.activity.update_summary()

            path = model.get_path(iter)
            model.remove(iter)

            # Select the next item, or else the last item.
            sel.select_path(path)
            if not sel.path_is_selected(path):
               row = path[0]-1
               if row >= 0: 
                   sel.select_path((row,))

# This is the main Finance activity class.
# 
# It owns the main application window, and all the various toolbars and options.
# Screens are stored in a stack, with the currently active screen on top.
class Finance(sugar.activity.activity.Activity):
    def __init__ (self, handle):
        sugar.activity.activity.Activity.__init__(self, handle)
        self.set_title(_("Finance"))

        # Initialize database.
        # data
        #   next_id
        #   transactions
        #     id, name, type, amount, date, category
        #   budgets 
        #     category, period, amount, budget
        self.data = {
            'next_id': 0,
            'transactions': [],
            'budgets': []
        }

        self.transaction_map = {}

        self.visible_transactions = []

        self.create_test_data()
  
        # Initialize view period to the first of the month.
        today = datetime.date.today()
        self.period_start = datetime.date(today.year, today.month, 1)

        # Create screens.
        self.register = RegisterScreen(self)
        self.chart = ChartScreen(self)
        self.budget = BudgetScreen(self)

        self.build_toolbox()
  
        self.screens = []
        self.screenbox = gtk.VBox()

        # Add the header.
        self.periodlabel = gtk.Label()

        headerbox = gtk.HBox()
        headerbox.pack_end(self.periodlabel, False, False)

        # Add the summary data.
        self.startlabel = gtk.Label()
        self.creditslabel = gtk.Label()
        self.debitslabel = gtk.Label()
        self.balancelabel = gtk.Label()

        summarybox = gtk.HBox()
        summarybox.pack_start(self.startlabel, True, False)
        summarybox.pack_start(self.creditslabel, True, False)
        summarybox.pack_start(self.debitslabel, True, False)
        summarybox.pack_start(self.balancelabel, True, False)

        vbox = gtk.VBox()

        vbox.pack_start(headerbox, False, False, 10)
        vbox.pack_start(gtk.HSeparator(), False, False, 0)
        vbox.pack_start(self.screenbox, True, True, 0)
        vbox.pack_start(summarybox, False, False, 10)

        # Start with the main screen.
        self.push_screen(self.register)

        # This has to happen last, because it calls the read_file method when restoring from the Journal.
        self.set_canvas(vbox)

        self.show_all()

        activity_toolbar = self.tbox.get_activity_toolbar()
        activity_toolbar.share.props.visible = False

    def build_toolbox(self):
        newcreditbtn = sugar.graphics.toolbutton.ToolButton('dialog-ok')
        newcreditbtn.set_tooltip(_("New Credit"))
        newcreditbtn.connect('clicked', self.register.newcredit_cb)

        newdebitbtn = sugar.graphics.toolbutton.ToolButton('dialog-ok')
        newdebitbtn.set_tooltip(_("New Debit"))
        newdebitbtn.connect('clicked', self.register.newdebit_cb)

        eraseitembtn = sugar.graphics.toolbutton.ToolButton('dialog-ok')
        eraseitembtn.set_tooltip(_("Erase Transaction"))
        eraseitembtn.connect('clicked', self.register.eraseitem_cb)

        self.registerbar = gtk.Toolbar()
        self.registerbar.insert(newcreditbtn, -1)
        self.registerbar.insert(newdebitbtn, -1)
        self.registerbar.insert(eraseitembtn, -1)
 
        self.chartbar = gtk.Toolbar()
        self.budgetbar = gtk.Toolbar()

        # Add common buttons to all toolbars.
        for bar in [self.registerbar, self.chartbar, self.budgetbar]:
            sep = gtk.SeparatorToolItem()
            sep.set_expand(True)
            sep.set_draw(False)

            thisperiodbtn = sugar.graphics.toolbutton.ToolButton('dialog-ok')
            thisperiodbtn.set_tooltip(_("This Month"))
            thisperiodbtn.connect('clicked', self.thisperiod_cb)

            prevperiodbtn = sugar.graphics.toolbutton.ToolButton('dialog-ok')
            prevperiodbtn.set_tooltip(_("Previous Month"))
            prevperiodbtn.connect('clicked', self.prevperiod_cb)

            nextperiodbtn = sugar.graphics.toolbutton.ToolButton('dialog-ok')
            nextperiodbtn.set_tooltip(_("Next Month"))
            nextperiodbtn.connect('clicked', self.nextperiod_cb)

            bar.insert(sep, -1)
            bar.insert(thisperiodbtn, -1)
            bar.insert(prevperiodbtn, -1)
            bar.insert(nextperiodbtn, -1)

        self.tbox = sugar.activity.activity.ActivityToolbox(self)
        self.tbox.add_toolbar(_('Register'), self.registerbar)
        self.tbox.add_toolbar(_('Chart'), self.chartbar)
        self.tbox.add_toolbar(_('Budget'), self.budgetbar)
        self.tbox.connect('current-toolbar-changed', self.tbox_cb)
        self.tbox.show_all()

        self.set_toolbox(self.tbox)

    def tbox_cb(self, widget, num):
        if num == 1 and self.screens[-1] != self.register:
            self.pop_screen()
            self.push_screen(self.register)

        if num == 2 and self.screens[-1] != self.chart:
            self.pop_screen()
            self.push_screen(self.chart)

        if num == 3 and self.screens[-1] != self.budget:
            self.pop_screen()
            self.push_screen(self.budget)

    def push_screen(self, screen):
        if len(self.screens):
            self.screenbox.remove(self.screens[-1])
 
        self.screenbox.pack_start(screen, True, True)
        self.screens.append(screen)

        self.build_screen()

    def pop_screen(self):
        self.screenbox.remove(self.screens[-1])
        self.screens.pop()
        if len(self.screens):
            self.screenbox.pack_start(self.screens[-1])

    def build_screen(self):
        self.build_visible_transactions()

        if len(self.screens):
            self.screens[-1].build()

        self.update_header()
        self.update_summary()

    def update_header(self):
        self.periodlabel.set_markup("<span size='xx-large'><b>" + self.period_start.strftime("%B, %Y") + "</b></span>")

    def update_summary(self):
        # Calculate starting balance.
        start = 0.0
        for t in self.data['transactions']:
            d = t['date']
            if d < self.period_start.toordinal():
                if t['type'] == 'credit':
                    start += t['amount'] 
                else:
                    start -= t['amount'] 

        # Calculate totals for this period.
        credit_count = 0
        credit_total = 0.0
        debit_count = 0
        debit_total = 0.0
        total = start 
        for t in self.visible_transactions:
            if t['type'] == 'credit':
                credit_count += 1
                credit_total += t['amount']
                total += t['amount']
            else:
                debit_count += 1
                debit_total += t['amount']
                total -= t['amount']

        # Update Balance.
        if total >= 0.0:
            balancecolor = '#4040ff'
        else:
            balancecolor = '#ff4040'
        balance = "<span size='xx-large' foreground='%s'><b>" % balancecolor 
        balance += _('Balance: ') + "%.2f" % total 
        balance += "</b></span>"
        self.balancelabel.set_markup(balance)

        self.startlabel.set_markup('Starting Balance: %.2f' % start)
        self.creditslabel.set_markup('%.2f in %d credits' % (credit_total, credit_count))
        self.debitslabel.set_markup('%.2f in %d debits' % (debit_total, debit_count))

    def thisperiod_cb(self, widget):
        today = datetime.date.today()
        self.period_start = datetime.date(today.year, today.month, 1)

        self.build_screen()

    def nextperiod_cb(self, widget):
        self.period_start = next_month(self.period_start) 
        self.build_screen()

    def prevperiod_cb(self, widget):
        self.period_start = prev_month(self.period_start) 
        self.build_screen()

    def build_visible_transactions(self):
        period_start_ord = self.period_start.toordinal()
        period_end_ord = next_month(self.period_start).toordinal()

        self.visible_transactions = []
        for t in self.data['transactions']:
            d = t['date']
            if d >= period_start_ord and d < period_end_ord:
                self.visible_transactions.append(t)

    def build_transaction_map(self):
        self.transaction_map = {}
        for t in self.data['transactions']:
            self.transaction_map[t['id']] = t

    def create_transaction(self, name, type, amount):
        id = self.data['next_id']
        self.data['next_id'] += 1

        t = {
            'id': id,
            'name': name,
            'type': type,
            'amount': amount,
            'date': datetime.date.today().toordinal(),
            'category': ''
        }
        self.data['transactions'].append(t)
        self.transaction_map[id] = t

        return id

    def destroy_transaction(self, id):
        t = self.transaction_map[id]
        self.data['transactions'].remove(t)
        del self.transaction_map[id]

    def create_test_data(self):
        self.data['transactions'].append({
            'id': -1,
            'name': 'Initial Balance',
            'type': 'credit',
            'amount': 200,
            'date': datetime.date.today().toordinal(),
            'category': 'Initial Balance'
        })
        self.data['transactions'].append({
            'id': -2,
            'name': 'Fix Car',
            'type': 'debit',
            'amount': 75,
            'date': datetime.date.today().toordinal(),
            'category': 'Transportation'
        })
        self.data['transactions'].append({
            'id': -3,
            'name': 'Adopt Cat',
            'type': 'debit',
            'amount': 100,
            'date': datetime.date.today().toordinal(),
            'category': 'Pets'
        })
        self.data['transactions'].append({
            'id': -4,
            'name': 'Buy New Clothes',
            'type': 'debit',
            'amount': 20,
            'date': datetime.date.today().toordinal(),
            'category': 'Clothing'
        })

        self.build_transaction_map()

    def read_file(self, file_path):
        # Load document.
        if self.metadata['mime_type'] != 'text/plain':
            return

        fd = open(file_path, 'r')
        try:
            text = fd.read()
            print "read %s" % text
            self.data = json.read(text)
        finally:
            fd.close()

        self.build_transaction_map()
        self.build_screen()

    def write_file(self, file_path):
        # Save document.
        if not self.metadata['mime_type']:
            self.metadata['mime_type'] = 'text/plain'

        fd = open(file_path, 'w')
        try:
            text = json.write(self.data)
            fd.write(text)
            print "wrote %s" % text
        finally:
            fd.close()
