### Fedora Core 26, 27 and 28

**Note that other versions of Fedora Core are not supported at this time.**

To install plaso and dependencies from the GIFT Cool Other Package Repo (COPR) you'll need to have dnf plugins installed:

```
sudo dnf install dnf-plugins-core
```

Add the [GIFT COPR](https://copr.fedorainfracloud.org/groups/g/gift/coprs/) to your dnf configuration:

```
sudo dnf copr enable @gift/stable
```

Install plaso, tools and dependencies:

```
sudo apt-get install python-plaso plaso-tools
```
