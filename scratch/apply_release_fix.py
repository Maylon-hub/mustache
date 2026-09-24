import os

def main():
    # 1. Update pyproject.toml in core-sg
    core_sg_pyproject = r'C:\Users\guest\Documents\GitHub\core-sg\pyproject.toml'
    with open(core_sg_pyproject, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update version to 0.4.2
    content = content.replace('version = "0.4.0"', 'version = "0.4.2"')
    content = content.replace('version = "0.4.1"', 'version = "0.4.2"')

    # Remove test-requires line
    content = content.replace('test-requires = ["scikit-learn>=1.3", "numpy>=1.24,<3", "pandas>=2.0"]\n', '')
    content = content.replace('test-requires = ["scikit-learn>=1.3", "numpy>=1.24,<3", "pandas>=2.0"]', '')

    # Update manylinux image to manylinux_2_28
    content = content.replace('manylinux-x86_64-image = "manylinux2014"', 'manylinux-x86_64-image = "manylinux_2_28"')

    with open(core_sg_pyproject, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Updated core-sg pyproject.toml to v0.4.2 and manylinux_2_28 successfully.")

    # 2. Update pyproject.toml in mustache
    mustache_pyproject = r'C:\Users\guest\Documents\GitHub\mustache\pyproject.toml'
    with open(mustache_pyproject, 'r', encoding='utf-8') as f:
        m_content = f.read()

    m_content = m_content.replace('core-sg-mustache>=0.4.0', 'core-sg-mustache>=0.4.2')
    m_content = m_content.replace('core-sg-mustache>=0.4.1', 'core-sg-mustache>=0.4.2')

    with open(mustache_pyproject, 'w', encoding='utf-8') as f:
        f.write(m_content)

    print("Updated mustache pyproject.toml dependency to >=0.4.2 successfully.")

if __name__ == "__main__":
    main()
