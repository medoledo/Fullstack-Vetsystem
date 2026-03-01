with open('c:/Users/medol/OneDrive/Desktop/vet/vetsystem/templates/inventorypage/inventory.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Status filter dropdown
cat_dropdown_end = '''            {% endfor %}
        </select>'''
status_dropdown = '''            {% endfor %}
        </select>
        <select name="status" class="form-select form-select-sm" style="max-width:200px;" onchange="this.form.submit()">
            <option value="">All Statuses</option>
            <option value="low_stock" {% if status_filter == 'low_stock' %}selected{% endif %}>Low Stock Only</option>
            <option value="expiring_soon" {% if status_filter == 'expiring_soon' %}selected{% endif %}>Expiring Soon</option>
        </select>'''
if 'name="status"' not in html:
    html = html.replace(cat_dropdown_end, status_dropdown, 1)

# fix the 'Clear' button logic
html = html.replace('{% if search_q or category_filter %}', '{% if search_q or category_filter or status_filter %}')

# 2. Add Item Unit dropdown
add_unit_old = '''<input type="text" name="unit" class="form-control" placeholder="e.g. bottles, vials">'''
add_unit_new = '''<select name="unit" class="form-select">
                                <option value=""> Select Unit </option>
                                {% for val, label in unit_choices %}
                                <option value="{{ val }}">{{ label }}</option>
                                {% endfor %}
                            </select>'''
html = html.replace(add_unit_old, add_unit_new)

# Edit Item Unit dropdown
edit_unit_old = '''<input type="text" name="unit" class="form-control" value="{{ d.item.unit }}">'''
edit_unit_new = '''<select name="unit" class="form-select">
                                <option value=""> Select Unit </option>
                                {% for val, label in unit_choices %}
                                <option value="{{ val }}" {% if d.item.unit == val %}selected{% endif %}>{{ label }}</option>
                                {% endfor %}
                            </select>'''
html = html.replace(edit_unit_old, edit_unit_new)

# 3. 3-dots actions (Items)
item_actions_old = '''<td class="text-end" style="white-space:nowrap;">
                            <button class="btn btn-outline-success btn-icon me-1" data-bs-toggle="modal" data-bs-target="#addBatchModal{{ d.item.id }}" title="Add Batch"><i class="fa-solid fa-layer-plus"></i></button>
                            <button class="btn btn-outline-primary btn-icon me-1" data-bs-toggle="modal" data-bs-target="#editItemModal{{ d.item.id }}" title="Edit Item"><i class="fa-solid fa-pen-to-square"></i></button>
                            <button class="btn btn-outline-danger btn-icon" data-bs-toggle="modal" data-bs-target="#deleteItemModal{{ d.item.id }}" title="Delete Item"><i class="fa-solid fa-trash"></i></button>
                        </td>'''
item_actions_new = '''<td class="text-end" style="white-space:nowrap;">
                            <div class="dropdown">
                                <button class="btn btn-light btn-sm px-2" type="button" data-bs-toggle="dropdown">
                                    <i class="fa-solid fa-ellipsis-vertical"></i>
                                </button>
                                <ul class="dropdown-menu dropdown-menu-end shadow-sm border-0">
                                    <li><a class="dropdown-item" href="#" data-bs-toggle="modal" data-bs-target="#addBatchModal{{ d.item.id }}"><i class="fa-solid fa-layer-plus me-2 text-success"></i> Add Batch</a></li>
                                    <li><a class="dropdown-item" href="#" data-bs-toggle="modal" data-bs-target="#editItemModal{{ d.item.id }}"><i class="fa-solid fa-pen-to-square me-2 text-primary"></i> Edit Item</a></li>
                                    <li><hr class="dropdown-divider"></li>
                                    <li><a class="dropdown-item text-danger" href="#" data-bs-toggle="modal" data-bs-target="#deleteItemModal{{ d.item.id }}"><i class="fa-solid fa-trash me-2"></i> Delete Item</a></li>
                                </ul>
                            </div>
                        </td>'''
html = html.replace(item_actions_old, item_actions_new)

# 3-dots actions (Batches)
batch_actions_old = '''<td class="text-end pe-3" style="white-space:nowrap;">
                                        <button class="btn btn-outline-primary btn-icon me-1" data-bs-toggle="modal" data-bs-target="#editBatchModal{{ batch.id }}" title="Edit batch"><i class="fa-solid fa-pen-to-square"></i></button>
                                        <button class="btn btn-outline-danger btn-icon" data-bs-toggle="modal" data-bs-target="#deleteBatchModal{{ batch.id }}" title="Delete batch"><i class="fa-solid fa-trash"></i></button>
                                    </td>'''
batch_actions_new = '''<td class="text-end pe-3" style="white-space:nowrap;">
                                        <div class="dropdown">
                                            <button class="btn btn-light btn-sm px-2" type="button" data-bs-toggle="dropdown">
                                                <i class="fa-solid fa-ellipsis-vertical"></i>
                                            </button>
                                            <ul class="dropdown-menu dropdown-menu-end shadow-sm border-0">
                                                <li><a class="dropdown-item" href="#" data-bs-toggle="modal" data-bs-target="#editBatchModal{{ batch.id }}"><i class="fa-solid fa-pen-to-square me-2 text-primary"></i> Edit Batch</a></li>
                                                <li><hr class="dropdown-divider"></li>
                                                <li><a class="dropdown-item text-danger" href="#" data-bs-toggle="modal" data-bs-target="#deleteBatchModal{{ batch.id }}"><i class="fa-solid fa-trash me-2"></i> Delete Batch</a></li>
                                            </ul>
                                        </div>
                                    </td>'''
html = html.replace(batch_actions_old, batch_actions_new)

# 3-dots actions (Categories)
cat_actions_old = '''<td class="text-end">
                            <button class="btn btn-outline-primary btn-icon me-1" data-bs-toggle="modal" data-bs-target="#editCatModal{{ cat.id }}"><i class="fa-solid fa-pen-to-square"></i></button>
                            <button class="btn btn-outline-danger btn-icon" data-bs-toggle="modal" data-bs-target="#deleteCatModal{{ cat.id }}"><i class="fa-solid fa-trash"></i></button>
                        </td>'''
cat_actions_new = '''<td class="text-end">
                            <div class="dropdown">
                                <button class="btn btn-light btn-sm px-2" type="button" data-bs-toggle="dropdown">
                                    <i class="fa-solid fa-ellipsis-vertical"></i>
                                </button>
                                <ul class="dropdown-menu dropdown-menu-end shadow-sm border-0">
                                    <li><a class="dropdown-item" href="#" data-bs-toggle="modal" data-bs-target="#editCatModal{{ cat.id }}"><i class="fa-solid fa-pen-to-square me-2 text-primary"></i> Edit Category</a></li>
                                    <li><hr class="dropdown-divider"></li>
                                    <li><a class="dropdown-item text-danger" href="#" data-bs-toggle="modal" data-bs-target="#deleteCatModal{{ cat.id }}"><i class="fa-solid fa-trash me-2"></i> Delete Category</a></li>
                                </ul>
                            </div>
                        </td>'''
html = html.replace(cat_actions_old, cat_actions_new)

with open('c:/Users/medol/OneDrive/Desktop/vet/vetsystem/templates/inventorypage/inventory.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('inventory.html successfully updated!')