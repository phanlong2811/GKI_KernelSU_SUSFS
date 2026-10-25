#!/usr/bin/env python3
"""Rewrite the SUSFS 6.12 patch's show_smaps_rollup hunks for sublevel < 92.

susfs4ksu bd275689 ("rebase susfs patches onto android16-6.12.92") rewrote the
fs/proc/task_mmu.c show_smaps_rollup SUS_MAP hunks against the 6.12.92 refactor
(proc_get_vma / smap_gather_stats(priv, vma, &mss)). Older 6.12 sublevels still
have the do { ... } for_each_vma loop, so those two hunks reject. Swap them for
the pre-rebase hunks (susfs4ksu b213c541), which target the old loop shape.

Usage: susfs_612_pre92_rollup.py <50_add_susfs_in_gki-android16-6.12.patch>
"""
import re
import sys

NEW_HUNK_RE = re.compile(
    r"@@ -\d+,\d+ \+\d+,\d+ @@ static int show_smaps_rollup\(struct seq_file \*m, void \*v\)\n"
    r"(?:[ +-].*\n)*?"
    r"(?=@@ |diff --git |\Z)"
)

OLD_HUNKS = """\
@@ -1388,7 +1437,14 @@ static int show_smaps_rollup(struct seq_file *m, void *v)

 \tvma_start = vma->vm_start;
 \tdo {
+#ifdef CONFIG_KSU_SUSFS_SUS_MAP
+\t\tif (vma->vm_file && SUSFS_IS_INODE_SUS_MAP(file_inode(vma->vm_file)))
+\t\t\tgoto bypass_orig_flow;
+#endif // #ifdef CONFIG_KSU_SUSFS_SUS_MAP
 \t\tsmap_gather_stats(vma, &mss, 0);
+#ifdef CONFIG_KSU_SUSFS_SUS_MAP
+bypass_orig_flow:
+#endif // #ifdef CONFIG_KSU_SUSFS_SUS_MAP
 \t\tlast_vma_end = vma->vm_end;

 \t\t/*
@@ -1454,8 +1510,15 @@ static int show_smaps_rollup(struct seq_file *m, void *v)

 \t\t\t/* Case 4 above */
 \t\t\tif (vma->vm_end > last_vma_end) {
+#ifdef CONFIG_KSU_SUSFS_SUS_MAP
+\t\t\t\tif (!vma->vm_file || !(SUSFS_IS_INODE_SUS_MAP(file_inode(vma->vm_file)))) {
+\t\t\t\t\tsmap_gather_stats(vma, &mss, last_vma_end);
+\t\t\t\t\tlast_vma_end = vma->vm_end;
+\t\t\t\t}
+#else
 \t\t\t\tsmap_gather_stats(vma, &mss, last_vma_end);
 \t\t\t\tlast_vma_end = vma->vm_end;
+#endif // #ifdef CONFIG_KSU_SUSFS_SUS_MAP
 \t\t\t}
 \t\t}
 \t} for_each_vma(vmi, vma);
"""


def main():
    path = sys.argv[1]
    text = open(path).read()
    if "smap_gather_stats(priv, vma, &mss)" not in text:
        print("SUSFS patch already targets the pre-92 show_smaps_rollup; nothing to do")
        return
    hunks = NEW_HUNK_RE.findall(text)
    if len(hunks) != 2:
        sys.exit(f"ERROR: expected 2 show_smaps_rollup hunks, found {len(hunks)}")
    text = text.replace(hunks[0], OLD_HUNKS, 1).replace(hunks[1], "", 1)
    open(path, "w").write(text)
    print("Replaced SUSFS show_smaps_rollup hunks with the pre-6.12.92 variant")


if __name__ == "__main__":
    main()
