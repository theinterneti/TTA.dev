// Logseq: [[TTA.dev/Platform_tta_dev/Components/Serena/Core/Test/Resources/Repos/Typescript/Test_repo/Index]]
export class DemoClass {
    value: number;
    constructor(value: number) {
        this.value = value;
    }
    printValue() {
        console.log(this.value);
    }
}

export function helperFunction() {
    const demo = new DemoClass(42);
    demo.printValue();
}

helperFunction();
