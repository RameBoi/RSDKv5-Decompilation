import re

path = "Game/dependencies/RSDKv5/RSDKv5/RSDK/Core/ModAPI.cpp"

shim = r"""#include <dirent.h>
#include <sys/stat.h>
#include <string.h>
#include <string>
#include <vector>

namespace fs
{
struct filesystem_error {
    const char *what() { return "filesystem error"; }
};

struct path {
    path() = default;
    path(std::string str) : pathStr(str) {}
    path(const char *str) : pathStr(str) {}
    const std::string &string() const { return pathStr; }
    path filename() const
    {
        size_t p = pathStr.find_last_of('/');
        return path(pathStr.substr(p == std::string::npos ? 0 : p + 1));
    }

private:
    std::string pathStr = "";
};

inline bool exists(path p)
{
    struct stat st;
    return stat(p.string().c_str(), &st) == 0;
}

inline bool is_directory(path p)
{
    struct stat st;
    return stat(p.string().c_str(), &st) == 0 && S_ISDIR(st.st_mode);
}

struct directory_entry {
    directory_entry() = default;
    directory_entry(fs::path p) : m_path(p) {}
    bool exists() const { return fs::exists(m_path); }
    bool is_directory() const { return fs::is_directory(m_path); }
    bool is_regular_file() const { return !fs::is_directory(m_path); }
    const fs::path &path() const { return m_path; }

private:
    fs::path m_path;
};

typedef std::vector<directory_entry> path_list;

enum class directory_options { follow_directory_symlink = 0 };

inline path_list directory_iterator(path p)
{
    path_list out;
    DIR *d = opendir(p.string().c_str());
    if (!d)
        return out;
    while (struct dirent *e = readdir(d)) {
        if (!strcmp(e->d_name, ".") || !strcmp(e->d_name, ".."))
            continue;
        out.push_back(directory_entry(fs::path(p.string() + "/" + e->d_name)));
    }
    closedir(d);
    return out;
}

inline void iosWalk(const std::string &dir, std::vector<directory_entry> &out, int depth)
{
    if (depth > 16)
        return;
    DIR *d = opendir(dir.c_str());
    if (!d)
        return;
    while (struct dirent *e = readdir(d)) {
        if (!strcmp(e->d_name, ".") || !strcmp(e->d_name, ".."))
            continue;
        std::string full = dir + "/" + e->d_name;
        out.push_back(directory_entry(fs::path(full)));
        if (fs::is_directory(fs::path(full)))
            iosWalk(full, out, depth + 1);
    }
    closedir(d);
}

struct recursive_directory_iterator {
    recursive_directory_iterator() = default;
    recursive_directory_iterator(path p, directory_options) { iosWalk(p.string(), entries, 0); }
    std::vector<directory_entry>::iterator begin() { return entries.begin(); }
    std::vector<directory_entry>::iterator end() { return entries.end(); }

private:
    std::vector<directory_entry> entries;
};
} // namespace fs
"""


def patch(s, pattern, make):
    new, n = re.subn(pattern, make, s, flags=re.M)
    if n != 1:
        raise SystemExit("PATCH FAILED (%d matches) for pattern %s" % (n, pattern))
    return new


s = open(path, newline="").read()
s = patch(s, r"^#include <filesystem>[ \t]*\r?$", lambda m: "#if RETRO_PLATFORM != RETRO_iOS\n#include <filesystem>\n#endif")
s = patch(s, r"^#if RETRO_PLATFORM != RETRO_ANDROID\r?\nnamespace fs = std::filesystem;",
          lambda m: "#if RETRO_PLATFORM == RETRO_iOS\n" + shim + "\n#elif RETRO_PLATFORM != RETRO_ANDROID\nnamespace fs = std::filesystem;")
open(path, "w", newline="").write(s)
print("mod loader patched for iOS")
