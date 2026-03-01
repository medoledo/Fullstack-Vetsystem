import sys

with open('c:/Users/medol/OneDrive/Desktop/vet/vetsystem/templates/inventorypage/inventory.html', 'r', encoding='utf-8') as f:
    text = f.read()

# We need to split the original text precisely where the corruption began:
# 'Line 480: <td style="min-width:140px;">'
split_token = '<td style="min-width:140px;">'
parts = text.split(split_token)
if len(parts) < 2:
    print('Split token not found')
    sys.exit(1)

head = parts[0] + split_token

# We need to split the original text where the corruption ended:
# 'Line 512: {% else %}' -> wait, that was in the Categories tab.
# We will just inject the entire remaining Items loop, Modals, and Categories Tab start.
# Let's find: '<div class="text-center py-5 text-muted">' which belongs to the end of Categories.
tail_token = '<div class="text-center py-5 text-muted">'
parts_tail = text.split(tail_token)
tail = tail_token + parts_tail[-1]

middle = '''
    {% if d.is_low_stock %}<span class="badge-low me-1"><i class="fa-solid fa-triangle-exclamation me-1"></i>Low Stock</span>{% endif %}
    {% if d.expiry_status == 'expired' %}<span class="badge-exp"><i class="fa-solid fa-skull-crossbones me-1"></i>Expired</span>{% elif d.expiry_status == 'warning' %}<span class="badge-warn"><i class="fa-solid fa-clock me-1"></i>Expiring Soon</span>{% elif d.expiry_status == 'ok' %}{% if not d.is_low_stock %}<span class="badge-ok"><i class="fa-solid fa-check me-1"></i>OK</span>{% endif %}{% endif %}
    {% if d.item.category.is_infinite %}<span class="badge-inf"><i class="fa-solid fa-check me-1"></i>OK</span>{% endif %}
</td>
{% if request.user|is_admin %}
<td class="text-end" style="white-space:nowrap;">
    <div class="dropdown">
        <button class="btn btn-light btn-sm px-2" type="button" data-bs-toggle="dropdown" data-bs-boundary="window">
            <i class="fa-solid fa-ellipsis-vertical"></i>
        </button>
        <ul class="dropdown-menu dropdown-menu-end shadow-sm border-0 z-3">
            <li><a class="dropdown-item" href="#" data-bs-toggle="modal" data-bs-target="#addBatchModal{{ d.item.id }}"><i class="fa-solid fa-layer-plus me-2 text-success"></i> Add Batch</a></li>
            <li><a class="dropdown-item" href="#" data-bs-toggle="modal" data-bs-target="#editItemModal{{ d.item.id }}"><i class="fa-solid fa-pen-to-square me-2 text-primary"></i> Edit Item</a></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item text-danger" href="#" data-bs-toggle="modal" data-bs-target="#deleteItemModal{{ d.item.id }}"><i class="fa-solid fa-trash me-2"></i> Delete Item</a></li>
        </ul>
    </div>
</td>
{% endif %}
</tr>
{% if d.batches %}
<tr id="batches-{{ d.item.id }}" class="batches-row bg-light" style="display:none;">
    <td colspan="{% if request.user|is_admin %}8{% else %}7{% endif %}" class="p-0 border-0">
        <div class="p-3">
            <div class="fw-semibold text-muted mb-2 ps-2" style="font-size:.8rem;text-transform:uppercase;">Batches for {{ d.item.name }}</div>
            <table class="table table-sm table-borderless mb-0">
                <thead class="text-muted" style="font-size:.85rem;">
                    <tr>
                        <th style="width:140px;">Date Received</th>
                        <th style="width:140px;">Quantity</th>
                        <th style="width:140px;">Expiration</th>
                        <th>Notes</th>
                        {% if request.user|is_admin %}<th class="text-end" style="width:100px;">Actions</th>{% endif %}
                    </tr>
                </thead>
                <tbody>
                    {% for batch in d.batches %}
                    <tr style="font-size:.9rem;">
                        <td class="text-dark">{{ batch.date_received|date:"d M Y" }}</td>
                        <td class="fw-medium">{{ batch.quantity }} {% if d.item.unit %}<span class="text-muted" style="font-size:.75rem;">{{ d.item.unit }}</span>{% endif %}</td>
                        <td>
                            {% if batch.expiration_date %}
                            <span class="{% if batch.expiration_date < today %}text-danger fw-bold{% elif batch.expiration_date <= warn_days %}text-warning fw-bold{% else %}text-muted{% endif %}">{{ batch.expiration_date|date:"d M Y" }}</span>
                            {% else %}{% endif %}
                        </td>
                        <td class="text-muted">{{ batch.notes|default:"" }}</td>
                        {% if request.user|is_admin %}
                        <td class="text-end pe-3" style="white-space:nowrap;">
                            <div class="dropdown">
                                <button class="btn btn-light btn-sm px-2" type="button" data-bs-toggle="dropdown" data-bs-boundary="window">
                                    <i class="fa-solid fa-ellipsis-vertical"></i>
                                </button>
                                <ul class="dropdown-menu dropdown-menu-end shadow-sm border-0 z-3">
                                    <li><a class="dropdown-item" href="#" data-bs-toggle="modal" data-bs-target="#editBatchModal{{ batch.id }}"><i class="fa-solid fa-pen-to-square me-2 text-primary"></i> Edit Batch</a></li>
                                    <li><hr class="dropdown-divider"></li>
                                    <li><a class="dropdown-item text-danger" href="#" data-bs-toggle="modal" data-bs-target="#deleteBatchModal{{ batch.id }}"><i class="fa-solid fa-trash me-2"></i> Delete Batch</a></li>
                                </ul>
                            </div>
                        </td>
                        {% endif %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </td>
</tr>
{% endif %}
{% endfor %}
                </tbody>
            </table>
        </div>
        
        <!-- Pagination -->
        {% if items_page.paginator.num_pages > 1 %}
        <div class="card-footer bg-white py-3 border-0">
            <nav>
                <ul class="pagination pagination-sm justify-content-center mb-0">
                    {% if items_page.has_previous %}
                    <li class="page-item"><a class="page-link" href="?tab=items&q={{ search_q }}&category={{ category_filter }}&status={{ status_filter }}&per_page={{ per_page }}&page={{ items_page.previous_page_number }}">Prev</a></li>
                    {% endif %}
                    {% for p in items_page.paginator.page_range %}
                    <li class="page-item {% if p == items_page.number %}active{% endif %}">
                        <a class="page-link" href="?tab=items&q={{ search_q }}&category={{ category_filter }}&status={{ status_filter }}&per_page={{ per_page }}&page={{ p }}">{{ p }}</a>
                    </li>
                    {% endfor %}
                    {% if items_page.has_next %}
                    <li class="page-item"><a class="page-link" href="?tab=items&q={{ search_q }}&category={{ category_filter }}&status={{ status_filter }}&per_page={{ per_page }}&page={{ items_page.next_page_number }}">Next</a></li>
                    {% endif %}
                </ul>
            </nav>
        </div>
        {% endif %}
        
        {% else %}
        <div class="text-center py-5 text-muted">
            <i class="fa-solid fa-box-open fa-3x mb-3 opacity-25"></i>
            <p class="mb-1 fw-semibold">No items found</p>
            <p class="small mb-0">Try changing your filters or add a new item.</p>
        </div>
        {% endif %}
    </div>
</div>
{% endif %} <!-- end items tab -->

<!--  TAB: CATEGORIES  -->
{% if tab == 'categories' %}
<div class="card">
    <div class="card-header d-flex align-items-center justify-content-between">
        <span><i class="fa-solid fa-folder me-2 text-success"></i> Categories</span>
        <span class="badge bg-secondary">{{ categories|length }} categor{{ categories|length|pluralize:"y,ies" }}</span>
    </div>
    <div class="card-body p-0">
        {% if categories %}
        <div class="table-responsive">
            <table class="table table-hover mb-0 inv-table">
                <thead class="table-light">
                    <tr>
                        <th>Category Name</th>
                        <th class="text-center">Infinite</th>
                        <th>Total Items</th>
                        {% if request.user|is_admin %}<th class="text-end">Actions</th>{% endif %}
                    </tr>
                </thead>
                <tbody>
                    {% for cat in categories %}
                    <tr>
                        <td class="fw-semibold text-dark">{{ cat.name }}</td>
                        <td class="text-center">
                            {% if cat.is_infinite %}
                            <i class="fa-solid fa-check text-success"></i>
                            {% else %}
                            <i class="fa-solid fa-minus text-muted opacity-50"></i>
                            {% endif %}
                        </td>
                        <td>{{ cat.items.count }} item{{ cat.items.count|pluralize }}</td>
                        {% if request.user|is_admin %}
                        <td class="text-end" style="white-space:nowrap;">
                            <div class="dropdown">
                                <button class="btn btn-light btn-sm px-2" type="button" data-bs-toggle="dropdown" data-bs-boundary="window">
                                    <i class="fa-solid fa-ellipsis-vertical"></i>
                                </button>
                                <ul class="dropdown-menu dropdown-menu-end shadow-sm border-0 z-3">
                                    <li><a class="dropdown-item" href="#" data-bs-toggle="modal" data-bs-target="#editCatModal{{ cat.id }}"><i class="fa-solid fa-pen-to-square me-2 text-primary"></i> Edit</a></li>
                                    <li><hr class="dropdown-divider"></li>
                                    <li><a class="dropdown-item text-danger" href="#" data-bs-toggle="modal" data-bs-target="#deleteCatModal{{ cat.id }}"><i class="fa-solid fa-trash me-2"></i> Delete</a></li>
                                </ul>
                            </div>
                        </td>
                        {% endif %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
'''

with open('c:/Users/medol/OneDrive/Desktop/vet/vetsystem/templates/inventorypage/inventory.html', 'w', encoding='utf-8') as f:
    f.write(head + middle + tail)

print("HTML Structure Restore Part 1 complete!")