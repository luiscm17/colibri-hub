-- Seed the recognized scope-definition catalog (§6.3).
-- These are product-versioned and immutable. Admin cannot create/edit them.

insert into public.access_scope_definitions (definition_key, scope_code, scope_name, owning_context, description, supported_actions) values
('warehouse.raw_materials', 'warehouse.raw_materials', 'Warehouse Raw Materials', 'Warehouse / Bale Management', 'Raw-material dashboard, detail, reception, and delivery', '{read,write,edit}'),
('warehouse.finished_products', 'warehouse.finished_products', 'Warehouse Finished Products', 'Warehouse / Finished Products', 'Finished-product dashboard, requirement, handoff issue, reception, availability, custody, dispatch, and return', '{read,write,edit}'),
('warehouse.production_supplies', 'warehouse.production_supplies', 'Warehouse Production Supplies', 'Warehouse / Production Supplies', 'Supplies dashboard, stock, reception, exits, and returns', '{read,write,edit}'),
('yarn_spinning.section.preparation', 'yarn_spinning.section.preparation', 'Yarn Spinning Preparation', 'Yarn Spinning / Preparation', 'Section dashboard, production, progress, and corrections', '{read,write,edit}'),
('yarn_spinning.section.ring_spinning', 'yarn_spinning.section.ring_spinning', 'Yarn Spinning Ring Spinning', 'Yarn Spinning / Ring Spinning', 'Section dashboard, production, progress, and corrections', '{read,write,edit}'),
('yarn_spinning.section.bobbin_winding', 'yarn_spinning.section.bobbin_winding', 'Yarn Spinning Bobbin Winding', 'Yarn Spinning / Bobbin Winding', 'Section dashboard, production, progress, and corrections', '{read,write,edit}'),
('yarn_spinning.section.twisting', 'yarn_spinning.section.twisting', 'Yarn Spinning Twisting', 'Yarn Spinning / Twisting', 'Section dashboard, production, progress, and corrections', '{read,write,edit}'),
('yarn_spinning.section.skeining', 'yarn_spinning.section.skeining', 'Yarn Spinning Skeining', 'Yarn Spinning / Skeining', 'Section dashboard, production, and corrections', '{read,write,edit}'),
('yarn_spinning.process_quality', 'yarn_spinning.process_quality', 'Yarn Spinning Process Quality', 'Yarn Spinning / Process Quality', 'Cross-section quality queries, records, and corrections', '{read,write,edit}'),
('yarn_spinning.waste', 'yarn_spinning.waste', 'Yarn Spinning Waste', 'Yarn Spinning / Waste', 'Cross-section waste queries, records, and corrections', '{read,write,edit}'),
('lot_processing', 'lot_processing', 'Lot Processing', 'Lot Processing', 'Dashboard, queue, detail, and transversal lifecycle information', '{read,write,edit}'),
('lot_processing.stage.inventory', 'lot_processing.stage.inventory', 'Lot Processing Inventory', 'Lot Processing / Inventory', 'Inventory-stage technical information and interventions', '{read,write,edit}'),
('lot_processing.stage.dyeing', 'lot_processing.stage.dyeing', 'Lot Processing Dyeing', 'Lot Processing / Dyeing', 'Dyeing-stage technical information and interventions', '{read,write,edit}'),
('lot_processing.stage.drying', 'lot_processing.stage.drying', 'Lot Processing Drying', 'Lot Processing / Drying', 'Drying-stage technical information and interventions', '{read,write,edit}'),
('lot_processing.stage.winding', 'lot_processing.stage.winding', 'Lot Processing Winding', 'Lot Processing / Winding', 'Winding-stage technical information and interventions', '{read,write,edit}'),
('lot_processing.stage.bagging', 'lot_processing.stage.bagging', 'Lot Processing Bagging', 'Lot Processing / Bagging', 'Bagging-stage technical information and interventions', '{read,write,edit}'),
('lot_processing.stage.quality', 'lot_processing.stage.quality', 'Lot Processing Quality', 'Lot Processing / Quality', 'Quality-stage technical information, release-for-reception actions, and handoff responses', '{read,write,edit}'),
('transversal.consolidated_dashboard', 'transversal.consolidated_dashboard', 'Consolidated Dashboard', 'Transversal reporting', 'Consolidated read model across authorized business information', '{read}'),
('access_control', 'access_control', 'Access Control', 'Access Control', 'Access administration and access-change history', '{manage_access}');
