# FAQ

## How to fix invalid signature error for Arch Linux?
>
> [!WARNING]
>
> I am not %100 sure about this solution but seems like the error is caused by outdated package database or keys. The recommended solution is to update your system's package database and upgrade all packages to ensure you have the latest keys and package versions. You can do this by running:
>
> ```bash
> sudo pacman -Syu
> ```
>
> Please refer to arch wiki for more detailed information about this issue and how to fix it. This is not an issue with the tool itself but with the package manager and the way it handles package signatures.
>
> I am not responsible any issue caused by this error or the way you choose to fix it. Please make sure to read the Arch Linux documentation and understand the implications of updating your system before proceeding.

Sometimes, when installing or updating packages on Arch Linux, you may encounter an error like this:

```bash
error: failed retrieving file 'ollama-cuda-0.17.1-1.1-x86_64_v3.pkg.tar.zst' from cdn77.cachyos.org : The requested URL returned error: 404
(3/3) checking keys in keyring                                                      [------------------------------------------------] 100%
(3/3) checking package integrity                                                    [------------------------------------------------] 100%
error: ollama: signature from "CachyOS <admin@cachyos.org>" is invalid
:: File /var/cache/pacman/pkg/ollama-0.17.1-1.1-x86_64_v3.pkg.tar.zst is corrupted (invalid or corrupted package (PGP signature)).
Do you want to delete it? [Y/n] 
error: ollama-cuda: signature from "CachyOS <admin@cachyos.org>" is invalid
:: File /var/cache/pacman/pkg/ollama-cuda-0.17.1-1.1-x86_64_v3.pkg.tar.zst is corrupted (invalid or corrupted package (PGP signature)).
Do you want to delete it? [Y/n] 
```
