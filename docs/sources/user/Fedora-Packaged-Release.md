# Fedora Packaged Release 

### Fedora 30 and 31

**Note that other versions of Fedora are not supported at this time.**

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
sudo dnf install plaso-tools
```
