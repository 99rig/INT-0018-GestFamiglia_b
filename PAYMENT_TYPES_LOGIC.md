# Logica di Calcolo delle Quote per Spese Parziali

## Panoramica

Questo documento descrive la logica di calcolo delle quote per le spese nei piani di spesa, in particolare per le spese di tipo "parziale" che vengono divise tra più membri della famiglia.

## Modelli Coinvolti

### 1. PlannedExpense (Spesa Pianificata)
Rappresenta una spesa programmata all'interno di un piano di spesa.

### 2. Expense (Pagamento Effettivo)
Rappresenta un pagamento reale effettuato per una spesa pianificata. Collegato a PlannedExpense tramite FK `planned_expense`.

## Tipi di Pagamento

### Campo: `payment_type`
Indica come la spesa viene divisa tra i membri:

```python
PAYMENT_TYPE_CHOICES = [
    ('shared', 'Condivisa'),      # Default: nessuna assegnazione specifica
    ('partial', 'Parziale'),       # Divisa tra membri (es. 60/40, 50/50)
    ('individual', 'Individuale'), # Pagata interamente da un solo membro
]
```

#### 1. **Shared (Condivisa)**
- La spesa è condivisa tra tutti i membri del piano
- Non viene tracciata una quota specifica per membro
- Utile per spese comuni (es. spesa al supermercato)
- `get_my_share()` restituisce €0.00

#### 2. **Individual (Individuale)**
- La spesa è pagata interamente da un singolo membro
- Il campo `paid_by_user` (FK a User) indica CHI paga
- `get_my_share()` restituisce l'importo totale se `paid_by_user == user_corrente`

#### 3. **Partial (Parziale)** ⭐
- La spesa è divisa tra due o più membri
- Ogni membro paga una quota specifica
- **La logica di calcolo è dinamica** (vedi sezione successiva)

## Campi per le Spese Parziali

### Campo: `paid_by_user`
```python
paid_by_user = models.ForeignKey(
    'users.User',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='individual_planned_expenses_paid',
    verbose_name="Pagata da",
    help_text="Utente che paga la spesa (solo per spese individuali)"
)
```

**Uso:**
- Solo per spese di tipo `individual`
- Identifica quale utente paga l'intera spesa
- Per spese `partial` → sempre `NULL`

### Campo: `my_share_amount`
```python
my_share_amount = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    null=True,
    blank=True,
    verbose_name="Mia Quota",
    help_text="Importo effettivamente pagato da me (solo per spese parziali)"
)
```

**Uso:**
- ⚠️ **DEPRECATO - Non più utilizzato nella logica di calcolo**
- Storico: serviva per memorizzare la quota manuale
- Ora il calcolo è dinamico dai pagamenti reali

## Logica di Calcolo: `get_my_share(user)`

Il metodo `get_my_share(user)` calcola dinamicamente la quota assegnata all'utente.

### Algoritmo

```python
def get_my_share(self, user=None):
    """Calcola la quota da pagare in base al payment_type

    Per spese parziali, calcola dinamicamente dalla somma dei pagamenti reali dell'utente.
    Se non ci sono pagamenti, usa il default (amount/2).
    """
    from decimal import Decimal

    if self.payment_type == 'individual':
        # Spesa individuale: pago tutto
        return self.amount

    elif self.payment_type == 'partial':
        # Spesa parziale: calcola dalla somma dei pagamenti reali
        if user:
            # Calcola dalla somma dei pagamenti effettivi dell'utente
            from apps.expenses.models import Expense
            total_paid_by_user = Expense.objects.filter(
                planned_expense=self,
                user=user
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

            if total_paid_by_user > 0:
                return total_paid_by_user

        # Se non ci sono pagamenti, usa my_share_amount se valorizzato
        if self.my_share_amount is not None:
            return self.my_share_amount

        # Altrimenti default: metà
        return self.amount / 2

    else:
        # Spesa condivisa: nessuna quota specifica
        return Decimal('0.00')
```

### Priorità di Calcolo (per `payment_type='partial'`)

1. **Pagamenti Reali** (massima priorità)
   - Somma di tutti i pagamenti (Expense) effettuati dall'utente per questa PlannedExpense
   - Se l'utente ha pagato €300 in totale → restituisce €300
   - **Questo è il valore che viene sempre usato quando ci sono pagamenti**

2. **Campo `my_share_amount`** (deprecato, fallback)
   - Se non ci sono pagamenti E `my_share_amount` è valorizzato
   - Usato per retrocompatibilità con dati precedenti

3. **Default: Metà** (ultima opzione)
   - Se non ci sono pagamenti E `my_share_amount` è NULL
   - Calcola `amount / 2`
   - Assume divisione equa tra due membri

## Esempi Pratici

### Esempio 1: Spesa con Pagamenti Multipli

```
PlannedExpense:
  description: "Spesa 1"
  amount: €500
  payment_type: 'partial'
  my_share_amount: €300 (ignorato)

Pagamenti (Expense):
  - User: Marco, amount: €300, date: 2025-09-28
  - User: Giulia, amount: €200, date: 2025-09-28

get_my_share(Marco) → €300 ✅ (somma pagamenti di Marco)
get_my_share(Giulia) → €200 ✅ (somma pagamenti di Giulia)
```

### Esempio 2: Modifica Pagamento

```
Situazione iniziale:
  PlannedExpense: €500, payment_type='partial'
  Pagamento: Marco paga €300

get_my_share(Marco) → €300

L'utente modifica il pagamento a €100:
  Pagamento aggiornato: Marco paga €100

get_my_share(Marco) → €100 ✅ (aggiornato automaticamente!)
```

### Esempio 3: Spesa Senza Pagamenti

```
PlannedExpense:
  description: "Spesa 5"
  amount: €250
  payment_type: 'partial'
  my_share_amount: NULL

Pagamenti: nessuno

get_my_share(Marco) → €125 (default: 250/2)
```

### Esempio 4: Aggiunta Secondo Pagamento

```
Situazione iniziale:
  PlannedExpense: €500, payment_type='partial'
  Pagamento 1: Marco paga €300

get_my_share(Marco) → €300

Giulia non riesce a pagare €200, paga solo €100.
Marco aggiunge un secondo pagamento di €100:

  Pagamento 1: Marco €300
  Pagamento 2: Marco €100

get_my_share(Marco) → €400 ✅ (300 + 100 = somma automatica!)
```

## Calcolo del Totale "Mie Spese"

Il widget "Mie" nel frontend mostra il totale delle spese assegnate all'utente corrente.

### Metodo: `SpendingPlan.get_my_assigned_total(user)`

```python
def get_my_assigned_total(self, user):
    """Calcola il totale delle spese assegnate all'utente specificato

    Include:
    - Spese pianificate individuali (paid_by_user = user)
    - Quota delle spese pianificate parziali (my_share)
    - Spese effettive individuali associate al piano (paid_by_user = user)
    - Quota delle spese effettive parziali associate al piano
    """
    from apps.expenses.models import Expense

    total = Decimal('0.00')

    # Spese pianificate
    for planned_expense in self.planned_expenses.all():
        if planned_expense.payment_type == 'individual' and planned_expense.paid_by_user_id == user.id:
            total += planned_expense.amount
        elif planned_expense.payment_type == 'partial':
            total += planned_expense.get_my_share(user)  # ← Chiamata dinamica

    # Spese effettive (non pianificate) associate al piano
    expenses = Expense.objects.filter(spending_plan=self)
    for expense in expenses:
        if expense.payment_type == 'individual' and expense.paid_by_user_id == user.id:
            total += expense.amount
        elif expense.payment_type == 'partial':
            total += expense.get_my_share()

    return total
```

### Esempio di Calcolo Totale

```
Piano: Settembre 2025

Spese:
1. Spesa 1 (partial): €500 → Marco ha pagato €300 → contribuisce €300
2. Spesa 5 (partial): €250 → nessun pagamento → contribuisce €125 (default)
3. spesa 2 (individual, paid_by=Marco): €133 → contribuisce €133
4. spesa 3 (individual, paid_by=Marco): €388 → contribuisce €388

TOTALE MIE: €300 + €125 + €133 + €388 = €946 ✅
```

## Sincronizzazione Automatica

### ✅ Cosa Funziona Automaticamente

1. **Aggiunta Pagamento**
   - Aggiungi un pagamento di €100
   - `get_my_share()` aggiorna automaticamente il calcolo
   - Widget "Mie" si aggiorna automaticamente

2. **Modifica Pagamento**
   - Cambi un pagamento da €300 a €100
   - `get_my_share()` ricalcola automaticamente
   - Widget "Mie" si aggiorna automaticamente

3. **Eliminazione Pagamento**
   - Elimini un pagamento di €100
   - `get_my_share()` esclude automaticamente quel pagamento
   - Widget "Mie" si aggiorna automaticamente

### ⚠️ Cosa NON Succede

Il campo `my_share_amount` nel database NON viene aggiornato automaticamente.
- È un campo statico che rimane invariato
- Viene ignorato quando ci sono pagamenti reali
- Serve solo come fallback quando non ci sono pagamenti

## Vantaggi di Questo Approccio

### 1. **Single Source of Truth**
- I pagamenti effettivi (Expense) sono l'unica fonte di verità
- Nessuna duplicazione di dati tra `my_share_amount` e pagamenti

### 2. **Aggiornamento Automatico**
- Modifichi un pagamento → quota aggiornata automaticamente
- Nessuna sincronizzazione manuale necessaria

### 3. **Flessibilità**
- Supporta divisioni non equali (60/40, 70/30, etc.)
- Supporta pagamenti multipli dallo stesso utente
- Supporta correzioni e modifiche senza complicazioni

### 4. **Retrocompatibilità**
- Il campo `my_share_amount` esiste ancora nel DB
- Dati vecchi continuano a funzionare
- Possibile migrazione graduale

## Serializer e API

### PlannedExpenseSerializer

Il serializer espone il campo calcolato `my_share`:

```python
class PlannedExpenseSerializer(serializers.ModelSerializer):
    my_share = serializers.SerializerMethodField()
    other_share = serializers.SerializerMethodField()

    def get_my_share(self, obj):
        """Calcola la quota da pagare"""
        request = self.context.get('request')
        user = request.user if request else None
        return str(obj.get_my_share(user))  # ← Passa l'utente corrente
```

### Risposta API

```json
{
  "id": 12,
  "description": "Spesa 1",
  "amount": "500.00",
  "payment_type": "partial",
  "my_share_amount": "300.00",  // ← Campo DB (ignorato se ci sono pagamenti)
  "my_share": "100.00",         // ← Valore calcolato dinamicamente
  "other_share": "400.00"       // ← Calcolato come amount - my_share
}
```

## Frontend

Il frontend usa il campo calcolato `my_share` restituito dall'API:

```javascript
const myAssignedExpenses = computed(() => {
  // Usa il valore calcolato dal backend
  return parseFloat(currentPlan.value?.my_assigned_total || 0)
})
```

### Aggiornamento Widget "Mie"

Quando cambi il tipo di pagamento (swipe o menu), il frontend:
1. Invia PATCH a `/planned-expenses/{id}/`
2. Ricarica il piano con `loadPlanData()`
3. Il backend ricalcola `my_assigned_total` automaticamente
4. Il widget "Mie" si aggiorna con il nuovo valore

## Considerazioni Future

### Possibili Miglioramenti

1. **Campo Calcolato Virtuale**
   - Considerare `@property` invece di metodo
   - Pro: sintassi più pulita
   - Contro: non può ricevere parametri (user)

2. **Cache dei Calcoli**
   - Memorizzare risultato in cache per query multiple
   - Invalidare cache quando cambiano pagamenti

3. **Rimozione `my_share_amount`**
   - Dopo migrazione completa, rimuovere il campo dal DB
   - Richiederebbe migrazione dati per casi edge

4. **Supporto Multi-Utente**
   - Attualmente assume massimo 2 membri per spesa parziale
   - Possibile estensione a N membri con quote personalizzate

## Migrazione Dati Esistenti

Per dati esistenti con `my_share_amount` popolato ma senza pagamenti:

```python
# Script di migrazione (esempio)
from apps.reports.models import PlannedExpense

# Trova spese parziali con my_share_amount ma senza pagamenti
for expense in PlannedExpense.objects.filter(payment_type='partial', my_share_amount__isnull=False):
    payments_count = expense.get_related_expenses().count()
    if payments_count == 0:
        # my_share_amount sarà usato come fallback
        # Nessuna azione necessaria
        pass
    else:
        # I pagamenti esistono, my_share_amount sarà ignorato
        # Nessuna azione necessaria
        pass
```

## Domande Frequenti (FAQ)

### Q: Perché non eliminare `my_share_amount`?
**A:** Retrocompatibilità. Dati vecchi potrebbero avere solo questo campo popolato. Serve come fallback.

### Q: Cosa succede se modifico `my_share_amount` via admin?
**A:** Il valore viene ignorato se esistono pagamenti reali. Viene usato solo se non ci sono pagamenti.

### Q: Come faccio a "resettare" la quota a metà?
**A:** Elimina tutti i pagamenti dell'utente. Il sistema calcolerà automaticamente amount/2.

### Q: Posso avere divisioni non equali (es. 60/40)?
**A:** Sì! Basta che gli utenti creino pagamenti con gli importi corretti (€300/€200 per una spesa di €500).

### Q: Cosa succede se la somma dei pagamenti supera l'importo totale?
**A:** Il sistema permette overpayment. `get_my_share()` restituisce la somma effettiva pagata dall'utente.

---

**Ultimo aggiornamento:** 2025-10-03
**Versione:** 1.0
