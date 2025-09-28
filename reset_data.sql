-- Reset completo di tutti i dati di spese e piani
-- Eseguire in ordine per rispettare le foreign key

-- 1. Elimina quote (dipendono dalle spese)
DELETE FROM expenses_expensequota;

-- 2. Elimina spese (possono dipendere dalle spese pianificate)
DELETE FROM expenses_expense;

-- 3. Elimina spese pianificate (dipendono dai piani)
DELETE FROM reports_plannedexpense;

-- 4. Elimina piani di spesa
DELETE FROM reports_spendingplan;

-- Verifica che tutto sia vuoto
SELECT 'ExpenseQuota' as tabella, COUNT(*) as records FROM expenses_expensequota
UNION ALL
SELECT 'Expense', COUNT(*) FROM expenses_expense
UNION ALL
SELECT 'PlannedExpense', COUNT(*) FROM reports_plannedexpense
UNION ALL
SELECT 'SpendingPlan', COUNT(*) FROM reports_spendingplan;

-- Reset sequenze per ripartire da 1
ALTER SEQUENCE expenses_expensequota_id_seq RESTART WITH 1;
ALTER SEQUENCE expenses_expense_id_seq RESTART WITH 1;
ALTER SEQUENCE reports_plannedexpense_id_seq RESTART WITH 1;
ALTER SEQUENCE reports_spendingplan_id_seq RESTART WITH 1;