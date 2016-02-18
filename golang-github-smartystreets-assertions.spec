%{?scl:%scl_package %{name}}

%if 0%{?fedora} || 0%{?rhel} == 6|| 0%{?rhel} == 7
%global with_devel 1
%global with_bundled 0
%global with_debug 0
# cyclic dependency between golang-github-smartystreets-goconvey and
# golang-github-smartystreets-assertions
%global with_check 0
%global with_unit_test 1
%else
%global with_devel 0
%global with_bundled 0
%global with_debug 0
%global with_check 0
%global with_unit_test 0
%endif

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%define copying() \
%if 0%{?fedora} >= 21 || 0%{?rhel} >= 7 \
%license %{*} \
%else \
%doc %{*} \
%endif

%global provider        github
%global provider_tld    com
%global project         smartystreets
%global repo            assertions
# https://github.com/smartystreets/assertions
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}
%global commit          4727d767ce8a81811c40eedc2a836c85aebb4d09
%global shortcommit     %(c=%{commit}; echo ${c:0:7})

Name:           %{?scl_prefix}golang-%{provider}-%{project}-%{repo}
Version:        0
Release:        0.6.git%{shortcommit}%{?dist}
Summary:        Fluent assertion-style functions
License:        MIT
URL:            https://%{provider_prefix}
Source0:        https://%{provider_prefix}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz

# If go_arches not defined fall through to implicit golang archs
%if 0%{?go_arches:1}
ExclusiveArch:  %{go_arches}
%else
ExclusiveArch:   %{ix86} x86_64 %{arm}
%endif
# If gccgo_arches does not fit or is not defined fall through to golang
%ifarch 0%{?gccgo_arches}
BuildRequires:   gcc-go >= %{gccgo_min_vers}
%else
BuildRequires:   golang
%endif

%description
%{summary}

%if 0%{?with_devel}
%package devel
Summary:       %{summary}
BuildArch:     noarch

%if 0%{?with_check}
BuildRequires: %{?scl_prefix}golang(github.com/smartystreets/goconvey/convey/reporting)
%endif

# cyclic dependency between golang-github-smartystreets-goconvey and
# golang-github-smartystreets-assertions
#BuildRequires: %{?scl_prefix}golang(github.com/smartystreets/goconvey/convey/reporting)

Requires: %{?scl_prefix}golang(github.com/smartystreets/goconvey/convey/reporting)

Provides:      %{?scl_prefix}golang(%{import_path}) = %{version}-%{release}
Provides:      %{?scl_prefix}golang(%{import_path}/should) = %{version}-%{release}

%description devel
%{summary}

This package contains library source intended for
building other packages which use import path with
%{import_path} prefix.
%endif

%if 0%{?with_unit_test}
%package unit-test
Summary:         Unit tests for %{name} package
# If go_arches not defined fall through to implicit golang archs
%if 0%{?go_arches:1}
ExclusiveArch:  %{go_arches}
%else
ExclusiveArch:   %{ix86} x86_64 %{arm}
%endif
# If gccgo_arches does not fit or is not defined fall through to golang
%ifarch 0%{?gccgo_arches}
BuildRequires:   gcc-go >= %{gccgo_min_vers}
%else
BuildRequires:   golang
%endif

%if 0%{?with_check}
#Here comes all BuildRequires: PACKAGE the unit tests
#in %%check section need for running
%endif

# test subpackage tests code from devel subpackage
Requires:        %{name}-devel = %{version}-%{release}

%description unit-test
%{summary}

This package contains unit tests for project
providing packages with %{import_path} prefix.
%endif

%prep
%setup -q -n %{repo}-%{commit}

%build
%{?scl:scl enable %{scl} - << "EOF"}

%{?scl:EOF}
%install
%{?scl:scl enable %{scl} - << "EOF"}
# source codes for building projects
%if 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# find all *.go but no *_test.go files and generate devel.file-list
for file in $(find . -iname "*.go" \! -iname "*_test.go") ; do
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> devel.file-list
done
rm -rf internal/*/.gitignore
%endif

# testing files for this project
%if 0%{?with_unit_test}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# find all *_test.go files and generate unit-test.file-list
for file in $(find . -iname "*_test.go"); do
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> unit-test.file-list
done
%endif

%if 0%{?with_devel}
olddir=$(pwd)
pushd %{buildroot}/%{gopath}/src/%{import_path}
for file in $(find . -type d) ; do
    echo "%%dir %%{gopath}/src/%%{import_path}/$file" >> ${olddir}/devel.file-list
done
popd
echo "%%dir %%{gopath}/src/%{provider}.%{provider_tld}/%{project}" >> devel.file-list
echo "%%dir %%{gopath}/src/%{provider}.%{provider_tld}" >> devel.file-list

sort -u -o devel.file-list devel.file-list
%endif

%{?scl:EOF}
%check
%if 0%{?with_check} && 0%{?with_unit_test} && 0%{?with_devel}
%ifarch 0%{?gccgo_arches}
function gotest { %{gcc_go_test} "$@"; }
%else
%if 0%{?golang_test:1}
function gotest { %{golang_test} "$@"; }
%else
function gotest { go test "$@"; }
%endif
%endif

export GOPATH=%{buildroot}/%{gopath}:%{gopath}
gotest %{import_path}
gotest %{import_path}/internal/oglematchers
%endif

%if 0%{?with_devel}
%files devel -f devel.file-list
%copying LICENSE.md
%doc README.md
%endif

%if 0%{?with_unit_test}
%files unit-test -f unit-test.file-list
%copying LICENSE.md
%doc README.md
%endif

%changelog
* Wed Feb 3 2016 Marek Skalicky <mskalick@redhat.com> - 0-0.6.git4727d76
- Fixed directory ownership

* Mon Nov 09 2015 jchaloup <jchaloup@redhat.com> - 0-0.5.git4727d76
- Just rebuild
  related: #1250509

* Thu Aug 20 2015 jchaloup <jchaloup@redhat.com> - 0-0.4.git4727d76
- internal packages are not provided but are needed for building
  related: #1250509
  resolves: #1255155

* Mon Aug 17 2015 jchaloup <jchaloup@redhat.com> - 0-0.3.git4727d76
- internal packages can not be provided since go-1.5
  related: #1250509

* Mon Aug 10 2015 Fridolin Pokorny <fpokorny@redhat.com> - 0-0.2.git4727d76
- Update spec file to spec-2.0
  resolves: #1250509

* Thu Apr 23 2015 jchaloup <jchaloup@redhat.com> - 0-0.1.git4727d76
- First package for Fedora
  resolves: #1214816

