import re

with open('c:/Users/medol/OneDrive/Desktop/vet/vetsystem/templates/inventorypage/inventory.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Item Actions
item_pattern = r'<td[^>]*text-end[^>]*>.*?editItemModal\{\{ d\.item\.id \}\}.*?</td>'
item_new = '''<td class="text-end" style="white-space:nowrap;">
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
html = re.sub(item_pattern, item_new, html, flags=re.DOTALL)

# 2. Batch Actions
batch_pattern = r'<td[^>]*text-end[^>]*>.*?editBatchModal\{\{ batch\.id \}\}.*?</td>'
batch_new = '''<td class="text-end pe-3" style="white-space:nowrap;">
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
html = re.sub(batch_pattern, batch_new, html, flags=re.DOTALL)

# 3. Category Actions
cat_pattern = r'<td[^>]*text-end[^>]*>.*?editCatModal\{\{ cat\.id \}\}.*?</td>'
cat_new = '''<td class="text-end">
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
html = re.sub(cat_pattern, cat_new, html, flags=re.DOTALL)

with open('c:/Users/medol/OneDrive/Desktop/vet/vetsystem/templates/inventorypage/inventory.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('inventory.html actions replaced via regex!')