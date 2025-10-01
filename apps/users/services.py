"""
Servizi per la gestione degli inviti email
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import FamilyInvitation

User = get_user_model()


class InvitationEmailService:
    """Servizio per l'invio di email di invito alla famiglia"""

    @staticmethod
    def send_invitation_email(invitation: FamilyInvitation):
        """
        Invia email di invito in base al tipo di destinatario:
        - Se l'utente non esiste: invito alla registrazione
        - Se l'utente esiste: invito a unirsi alla famiglia
        """
        try:
            # Controlla se l'utente esiste già
            user_exists = User.objects.filter(email=invitation.email).exists()

            if user_exists:
                # Utente esistente - invito a unirsi alla famiglia
                return InvitationEmailService._send_join_family_email(invitation)
            else:
                # Nuovo utente - invito alla registrazione
                return InvitationEmailService._send_registration_email(invitation)

        except Exception as e:
            print(f"❌ Errore nell'invio email per {invitation.email}: {e}")
            return False

    @staticmethod
    def _send_registration_email(invitation: FamilyInvitation):
        """Invia email di invito alla registrazione per nuovi utenti"""
        subject = f"Invito alla famiglia {invitation.family.name} - My Crazy Family"

        # Template email professionale per registrazione
        message = f"""Gentile utente,

{invitation.invited_by.get_full_name()} ti ha invitato a unirti alla famiglia "{invitation.family.name}" sulla piattaforma My Crazy Family.

My Crazy Family è un'applicazione per la gestione condivisa delle spese familiari, che permette di:
• Monitorare e categorizzare le spese
• Gestire budget mensili
• Tenere traccia dei pagamenti condivisi
• Pianificare spese future

Per accettare l'invito e completare la registrazione:

1. Visita il sito: https://mycrisisfamily.com/
2. Completa la registrazione con questo indirizzo email
3. Accedi alle Impostazioni del tuo profilo
4. Seleziona "Unisciti con Codice"
5. Inserisci il seguente codice di invito: {invitation.token}

IMPORTANTE: Questo invito scade il {invitation.expires_at.strftime('%d/%m/%Y alle %H:%M')}.

Per assistenza o domande, non esitare a contattare {invitation.invited_by.get_full_name()}.

Cordiali saluti,
Il team di My Crazy Family

---
My Crazy Family - Gestione spese familiari
Questo è un messaggio automatico, si prega di non rispondere a questa email.
        """

        return send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=False
        )

    @staticmethod
    def _send_join_family_email(invitation: FamilyInvitation):
        """Invia email di invito a unirsi alla famiglia per utenti esistenti"""
        subject = f"Nuovo invito alla famiglia {invitation.family.name} - My Crazy Family"

        # Template email professionale per utenti esistenti
        message = f"""Gentile utente,

{invitation.invited_by.get_full_name()} ti ha invitato a unirti alla famiglia "{invitation.family.name}" sulla piattaforma My Crazy Family.

Avendo già un account registrato, puoi accettare immediatamente l'invito seguendo questi semplici passaggi:

1. Accedi alla tua applicazione: https://mycrisisfamily.com/
2. Naviga nel menu "Impostazioni"
3. Seleziona "Unisciti con Codice"
4. Inserisci il codice di invito: {invitation.token}

Una volta completato l'accesso alla famiglia, avrai accesso alle seguenti funzionalità condivise:
• Gestione spese e pagamenti
• Controllo budget familiari
• Pianificazione spese future
• Report e analisi delle spese

IMPORTANTE: Questo invito scade il {invitation.expires_at.strftime('%d/%m/%Y alle %H:%M')}.

Per qualsiasi difficoltà tecnica o domande, puoi contattare direttamente {invitation.invited_by.get_full_name()}.

Cordiali saluti,
Il team di My Crazy Family

---
My Crazy Family - Gestione spese familiari
Questo è un messaggio automatico, si prega di non rispondere a questa email.
        """

        return send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=False
        )