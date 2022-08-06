# Fedora Packaged Release

### Fedora 36

**Note that other versions of Fedora are not supported at this time.**

To install Plaso and dependencies from the GIFT Cool Other Package Repo (COPR)
you'll need to have dnf plugins installed:

```
sudo dnf install dnf-plugins-core
```

Add the [GIFT COPR](https://copr.fedorainfracloud.org/groups/g/gift/coprs/) to
your dnf configuration:

```
sudo dnf copr enable @gift/stable
```

Install Plaso, tools and dependencies:

```
sudo dnf install plaso-tools
```
