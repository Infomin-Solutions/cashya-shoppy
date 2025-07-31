from django.core.management.base import BaseCommand
from django.conf import settings
from authentication.utils import totp_manager


class Command(BaseCommand):
    help = 'Generate TOTP QR code for the application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-name',
            type=str,
            default=None,
            help='Custom account name for the TOTP (default: from settings)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='totp_qr.png',
            help='Output filename for the QR code image (default: totp_qr.png)'
        )
        parser.add_argument(
            '--show-uri',
            action='store_true',
            help='Display the provisioning URI instead of generating QR code'
        )

    def handle(self, *args, **options):
        account_name = options['account_name']
        output_file = options['output']
        show_uri = options['show_uri']

        try:
            if show_uri:
                # Just show the URI
                uri = totp_manager.get_provisioning_uri(account_name)
                self.stdout.write(
                    self.style.SUCCESS(f'TOTP Provisioning URI:\n{uri}')
                )
                self.stdout.write(
                    self.style.WARNING(
                        '\nYou can manually enter this URI in your authenticator app '
                        'or use it to generate a QR code.'
                    )
                )
            else:
                # Generate QR code
                qr_data = totp_manager.generate_qr_code(account_name)

                # Save to file
                with open(output_file, 'wb') as f:
                    f.write(qr_data)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'QR code generated successfully: {output_file}')
                )
                self.stdout.write(
                    self.style.WARNING(
                        f'Scan the QR code above or the saved file {output_file} with your authenticator app.'
                    )
                )

            # Show current TOTP info
            current_code = totp_manager.generate_4_digit_code()
            time_remaining = totp_manager.get_current_time_remaining()

            self.stdout.write('\n' + '='*50)
            self.stdout.write(f'Current 4-digit TOTP code: {current_code}')
            self.stdout.write(f'Time remaining: {time_remaining} seconds')
            self.stdout.write(f'TOTP Secret (Base64): {settings.TOTP_SECRET}')
            self.stdout.write(f'Issuer: {settings.TOTP_ISSUER_NAME}')
            self.stdout.write('='*50)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating TOTP QR code: {str(e)}')
            )
            return

        # Instructions
        self.stdout.write('\n' + self.style.WARNING('SETUP INSTRUCTIONS:'))
        self.stdout.write(
            '1. Install an authenticator app (Google Authenticator, Authy, etc.)')
        self.stdout.write(
            '2. Scan the QR code or manually enter the provisioning URI')
        self.stdout.write(
            '3. The app will generate 6-digit codes, but only use the first 4 digits')
        self.stdout.write('4. The codes change every 30 seconds')
        self.stdout.write(
            '\nNote: This system uses only the first 4 digits of the standard 6-digit TOTP codes.')
