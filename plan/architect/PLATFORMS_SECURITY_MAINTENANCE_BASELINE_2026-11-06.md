# Platforms, security and maintenance — baseline for every APCCS feature

Date: 2026-11-06, America/Vancouver. By Claude, as architect.
Status: STANDING DESIGN BASELINE (proposal). Not a batch. Every future batch should meet it.

## Owner's words (05:28)

> I want it to run in my phone but I also like it to work on any computer or Chromebook. Down the
> long run I like to make apk too for fun i know they need maintenance. [...] We do have to
> consider security and long-term maintenance to keep the program operating. That is a bare
> minimum there is no such thing as a non-maintenance program that I could think of.

## 1. Platforms: one program, every device

- **Core:** standard-library Python only (already a rule). The same files run on an Android
  phone (Termux), Windows, macOS, Linux, and a Chromebook through its built-in Linux environment.
  NOT CHECKED: managed or school Chromebooks can switch that environment off.
- **Screen:** one small local web page, served by the core on 127.0.0.1 and opened in any
  browser. One interface for phone, computer and Chromebook, with no separate code per device.
- **APK (later, optional):** a thin Android wrapper around the same web page. It adds Android
  upkeep (yearly platform updates, keeping the signing key safe), so it comes after the core is
  stable.

## 2. Security: layers, not one big tool

1. **Least power:** the program touches only allowed folders (A5), keeps no secrets in code
   or logs, and never sends case files off the device.
2. **Few dependencies:** the standard-library rule is also a security rule. There's nothing
   third-party in the core to be compromised.
3. **Checks on every change:** guard, tests, the A7 readability gate and secret masking (A4),
   run on GitHub's server.
4. **Device basics:** phone encryption and screen lock, and apps installed only from their
   official sources.
5. **Audit program (future project, out of scope now):** start small, as a weekly server
   recipe that scans for secrets, checks that file permissions and allowed paths still hold,
   and checks the Python version's support status. Grow it later into the full
   phone/computer audit program the Owner described. GitHub's own scanners are mostly free
   only for public repositories (NOT CHECKED for these private ones).

## 3. Maintenance: none is impossible, low is achievable

No program that connects to anything is maintenance-free: operating systems update, Python
versions reach end of life, AI providers change their interfaces, and security fixes appear.
The nearest thing to zero maintenance is plain data in open formats. Text, CSV, JSON and SQLite
files stay readable for decades even if the program stops. That's why APCCS keeps its records
in them.

Ways to keep upkeep low:
- Few dependencies (standard library), so fewer things break.
- An offline core that depends on no company.
- Adapters around every outside service, so a provider change breaks only that one adapter.
- Tests that catch breakage, plus a monthly server "health run" on the newest Python.
- Versions recorded, and changes made by reversible PRs.
- **Known deadline:** Python 3.11 (the current minimum) gets security fixes until about
  October 2027 (NOT CHECKED against python.org today). Plan the move to a newer minimum before
  then.
