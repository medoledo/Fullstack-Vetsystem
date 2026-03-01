import sys

with open('c:/Users/medol/OneDrive/Desktop/vet/vetsystem/templates/inventorypage/inventory.html', 'r', encoding='utf-8') as f:
    text = f.read()

# I will find the end block where the script tag is, and inject the modals before the script block.
marker = '<script>'
parts = text.split(marker)

modals = '''
<!--  MODALS: ITEMS & BATCHES  -->
{% for d in items_with_batches %}
<!-- Add Batch -->
<div class="modal fade" id="addBatchModal{{ d.item.id }}" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content border-0 shadow">
            <form method="post" action="{% url 'inventory_add_batch' d.item.id %}">
                {% csrf_token %}
                <div class="modal-header bg-light border-0">
                    <h5 class="modal-title fw-bold"><i class="fa-solid fa-layer-plus me-2 text-success"></i> Add Batch: {{ d.item.name }}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row g-3">
                        <div class="col-sm-6">
                            <label class="form-label fw-medium">Quantity</label>
                            <input type="number" step="0.01" class="form-control" name="quantity" required>
                        </div>
                        <div class="col-sm-6">
                            <label class="form-label fw-medium">Expiration Date</label>
                            <input type="date" class="form-control" name="expiration_date">
                        </div>
                        <div class="col-sm-6">
                            <label class="form-label fw-medium">Date Received</label>
                            <input type="date" class="form-control" name="date_received" value="{% now 'Y-m-d' %}" required>
                        </div>
                        <div class="col-12">
                            <label class="form-label fw-medium">Notes</label>
                            <textarea class="form-control" name="notes" rows="2"></textarea>
                        </div>
                    </div>
                </div>
                <div class="modal-footer border-0">
                    <button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary px-4"><i class="fa-solid fa-plus me-1"></i> Add Batch</button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Edit Item -->
<div class="modal fade" id="editItemModal{{ d.item.id }}" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content border-0 shadow">
            <form method="post" action="{% url 'inventory_item_edit' d.item.id %}">
                {% csrf_token %}
                <div class="modal-header bg-light border-0">
                    <h5 class="modal-title fw-bold"><i class="fa-solid fa-pen-to-square me-2 text-primary"></i> Edit Item: {{ d.item.name }}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row g-3">
                        <div class="col-12"><label class="form-label fw-medium">Name</label><input type="text" class="form-control" name="name" value="{{ d.item.name }}" required></div>
                        <div class="col-sm-6"><label class="form-label fw-medium">Category</label>
                            <select class="form-select" name="category" required>
                                {% for cat in categories %}<option value="{{ cat.id }}" {% if cat.id == d.item.category.id %}selected{% endif %}>{{ cat.name }}</option>{% endfor %}
                            </select></div>
                        <div class="col-sm-6"><label class="form-label fw-medium">Unit</label>
                            <select class="form-select" name="unit">
                                <option value="">-- None --</option>
                                {% for u_val, u_lbl in unit_choices %}
                                <option value="{{ u_val }}" {% if d.item.unit == u_val %}selected{% endif %}>{{ u_lbl }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-sm-6"><label class="form-label fw-medium">Price ($)</label><input type="number" step="0.01" class="form-control" name="price" value="{{ d.item.price }}" required></div>
                        <div class="col-12"><label class="form-label fw-medium">Notes</label><textarea class="form-control" name="notes" rows="2">{{ d.item.notes }}</textarea></div>
                    </div>
                </div>
                <div class="modal-footer border-0">
                    <button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save Changes</button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Delete Item -->
<div class="modal fade" id="deleteItemModal{{ d.item.id }}" tabindex="-1">
    <div class="modal-dialog modal-sm modal-dialog-centered">
        <div class="modal-content border-0 shadow">
            <div class="modal-header bg-danger text-white border-0">
                <h5 class="modal-title fw-bold">Delete Item</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body text-center py-4">
                <i class="fa-solid fa-triangle-exclamation text-danger fa-3x mb-3"></i>
                <p class="mb-0">Are you sure you want to delete <strong>{{ d.item.name }}</strong>?</p>
                <p class="text-muted small mt-2">This will also delete all associated batches. This action cannot be undone.</p>
            </div>
            <div class="modal-footer border-0 justify-content-center">
                <button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancel</button>
                <form method="post" action="{% url 'inventory_item_delete' d.item.id %}">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger px-4"><i class="fa-solid fa-trash me-1"></i>Delete</button>
                </form>
            </div>
        </div>
    </div>
</div>

<!-- Edit Batches -->
{% for batch in d.batches %}
<div class="modal fade" id="editBatchModal{{ batch.id }}" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content border-0 shadow">
            <form method="post" action="{% url 'inventory_batch_edit' batch.id %}">
                {% csrf_token %}
                <div class="modal-header bg-light border-0">
                    <h5 class="modal-title fw-bold"><i class="fa-solid fa-pen-to-square me-2 text-primary"></i> Edit Batch for {{ d.item.name }}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row g-3">
                        <div class="col-sm-6">
                            <label class="form-label fw-medium">Quantity</label>
                            <input type="number" step="0.01" class="form-control" name="quantity" value="{{ batch.quantity }}" required>
                        </div>
                        <div class="col-sm-6">
                            <label class="form-label fw-medium">Expiration Date</label>
                            <input type="date" class="form-control" name="expiration_date" value="{% if batch.expiration_date %}{{ batch.expiration_date|date:'Y-m-d' }}{% endif %}">
                        </div>
                        <div class="col-sm-6">
                            <label class="form-label fw-medium">Date Received</label>
                            <input type="date" class="form-control" name="date_received" value="{% if batch.date_received %}{{ batch.date_received|date:'Y-m-d' }}{% endif %}">
                        </div>
                        <div class="col-12">
                            <label class="form-label fw-medium">Notes</label>
                            <textarea class="form-control" name="notes" rows="2">{{ batch.notes }}</textarea>
                        </div>
                    </div>
                </div>
                <div class="modal-footer border-0">
                    <button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary px-4">Save Changes</button>
                </div>
            </form>
        </div>
    </div>
</div>

<div class="modal fade" id="deleteBatchModal{{ batch.id }}" tabindex="-1">
    <div class="modal-dialog modal-sm modal-dialog-centered">
        <div class="modal-content border-0 shadow">
            <div class="modal-header bg-danger text-white border-0">
                <h5 class="modal-title fw-bold">Delete Batch</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body text-center py-4">
                <p class="mb-0">Are you sure you want to delete this batch?</p>
            </div>
            <div class="modal-footer border-0 justify-content-center">
                <button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancel</button>
                <form method="post" action="{% url 'inventory_batch_delete' batch.id %}">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger px-4">Delete</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endfor %}
{% endfor %}

'''

new_text = parts[0] + modals + marker + parts[1]
with open('c:/Users/medol/OneDrive/Desktop/vet/vetsystem/templates/inventorypage/inventory.html', 'w', encoding='utf-8') as f:
    f.write(new_text)

print("Modals injected successfully!")