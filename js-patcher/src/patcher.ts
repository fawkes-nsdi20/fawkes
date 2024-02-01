/* MIT License
 *
 * Copyright (c) 2019 Shaghayegh Mardani
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

interface NativeUpdate {
    shift: number; // delete (-1) or insert (+1)
    cpid: number[]; // parent's cpid
    index: number; // where the target(child) is added to or removed from.
}

interface Edit {
    _type: string;
    cpid: number[];
    i: number; // target_index
    n: string; // tag_name
    attrs: object;
    c: (Array<Edit> | string);
    np: number[]; //new parent cpid
}

// JSON objects from Python
let jsonUpdates: Edit[] = [];
// DOM tree changes called from native scripts
let scriptUpdates: NativeUpdate[] = [];
// keep the already-applied native script updates for DOM ahead accesses
let nativeInserts: number[][] = [];
// keep track of what was the last applied update
let lastSeencpid: number[] = [0]
// is the applyUpdates called before?
let applyUpdatesCalled = false;
// The following functions are either the exact copy or modified versions
// of Ravi's code from:
// dependency_caching/blob/master/document_rewriting/inline.html

function getChildPath(node: Node | null): (number[] | null) {
    if (node == null) {
        // console.error('[Error] Cannot getChildPath for null!');
        return null;
    }
    let childPath: number[] = [];
    while (node.parentNode) {
        let children = node.parentNode.childNodes;
        for (let i = 0; i < children.length; ++i) {
            if (children[i] == node) {
                childPath.unshift(i);
                break;
            }
        }
        node = node.parentNode;
    }
    // if this is truly in the DOM, then node should be #document
    if (node === document)
        return childPath;

    return []; // return empty array instead  the relative child path
}

function getIndexOf(node: Node): number {
    // returns the index of node in its parent.childNodes list
    let index: number = 0;
    while ((node = node.previousSibling))
        ++index;
    return index;
}

function findNodeBycpid(childPathArr: number[]): (Node | null) {
    let current: Node = document;
    for (let i = 0; i < childPathArr.length; ++i) {
        if (childPathArr[i] < current.childNodes.length) {
            current = current.childNodes[childPathArr[i]];
        } else {
            // console.error('[Error] Looking for cpid=', childPathArr, ' at i=', i);
            return null;
        }
    }
    return current;
}

function isStrictPrefix(thiscpid: number[], thatcpid: number[]): boolean {
    // checks if thiscpid is a prefix of thatcpid, but not equal to it.
    if (thiscpid.length >= thatcpid.length)
        return false;
    let prefixed = true;
    for (let i = 0; i < thiscpid.length; i++) {
        if (thatcpid[i] != thiscpid[i])
            prefixed = false;
    }
    return prefixed;
}

function comparecpidPositions(first: number[], second: number[]): number {
    // Compares the second node cpid with the first one to see
    // which side of the first node, the second node is on.
    // The second node could be on the left/above (-1), on the right(1),
    // in the subtree(2) of, or equal(0) to the first node.
    let minLen = Math.min(first.length, second.length);
    for (let i = 0; i < minLen; i++) {
        if (second[i] < first[i])
            return -1;
        else if (second[i] > first[i])
            return 1;
    }
    // so far [0:minLen] has been equal, so if the second is above first
    // that means second node is an ancestor of the first node
    if (first.length < second.length)
        return 2;
    else if (first.length == second.length) //to cpids are equal
        return 0;
    else // the second node is an ancestor of the first node
        return -2;
}

function isEqualcpid(thiscpid: number[], thatcpid: number[]): boolean {
    if (!thiscpid || !thatcpid) // if either of them is null
        return false;
    if (thiscpid.length != thatcpid.length)
        return false;
    for (let i = 0; i < thiscpid.length; i++) {
        if (thiscpid[i] != thatcpid[i])
            return false;
    }
    return true;
}

function shouldBeSeen(current: number[], other: number[]): boolean {
    // if the other node should be seen from current position.
    if (comparecpidPositions(current, other) <= 0)
        return true;

    if (jsonUpdates.length) {
        updateJSONcpids();
    }
    for (let i = 0; i < nativeInserts.length; ++i) {
        // if other is either the nativeInserts[i] or in its subtree
        let compared = comparecpidPositions(other, nativeInserts[i]);
        if (compared == 0 || compared == -2)
            return true;
    }
    return false;
}

class MyHTMLCollectionOf<T extends Element> implements HTMLCollectionOf<T> {
    private original: HTMLCollectionOf<T>;
    private lastScriptcpid: number[];
    private underlying: Array<T>;
    [index: number]: T; //Index signature
    //TODO: index with names as well

    constructor(original: HTMLCollectionOf<T>) {
        this.original = original;
        this.lastScriptcpid = null;
        this.cutAheadDOM();
    }

    private cutAheadDOM() {
        if (document.currentScript != null) {
            let currentcpid: number[] = getChildPath(document.currentScript);
            if (isEqualcpid(currentcpid, this.lastScriptcpid))
                return; // nothing has changed since this function's last call.

            // lastScriptcpid has changed
            this.lastScriptcpid = currentcpid;
            let leftOfCut: Array<T> = [];
            for (let i = 0; i < this.original.length; ++i) {
                let elementcpid = getChildPath(this.original[i]); // == item(i)
                if (shouldBeSeen(currentcpid, elementcpid))
                    leftOfCut.push(this.original[i]);
                // else
                // break; // rest of the original elements are on the right side of DOM.
            }
            this.underlying = leftOfCut;
            // setting the scalar index
            for (let i = 0; i < this.underlying.length; ++i) {
                this[i] = this.underlying[i];
            }
        }
        else { // if currentScript is null, do not cut anything
            this.underlying = [];
            for (let i = 0; i < this.original.length; ++i) {
                this.underlying.push(this.original[i]);
                this[i] = this.original[i];
            }
        }
    }

    namedItem(name: string): (T | null) {
        if (document.currentScript == null) {
            return this.original.namedItem(name);
        } else {
            this.cutAheadDOM();
            let originalRes = this.original.namedItem(name);
            let resultcpid: number[] = getChildPath(originalRes);
            if (originalRes &&
                !shouldBeSeen(this.lastScriptcpid, resultcpid))
                return null; // should not see the original result
            else
                return originalRes;
        }
    }

    item(index: number): (T | null) {
        if (document.currentScript == null) {
            return this.original[index];
        } else {
            this.cutAheadDOM();
            return this[index] || null;
        }
    }
    //instead of readonly property, since we need to recompute each time.
    get length(): number {
        if (document.currentScript == null) {
            // this method is called inside a callback function ->
            // we could be anywhere in the DOM, therefore no cuts.
            return this.original.length;
        } else {
            this.cutAheadDOM();
            return this.underlying.length;
        }
    }
}

class MyNodeListOf<T extends Node> implements NodeListOf<T> {
    private original: NodeListOf<T>;
    private underlying: Array<T>;
    [index: number]: T;

    constructor(original: NodeListOf<T>) {
        this.original = original;
        this.cutAheadDOM();
    }

    private cutAheadDOM() {
        if (document.currentScript != null) {
            let currentcpid: number[] = getChildPath(document.currentScript);

            let leftOfCut: Array<T> = [];
            for (let i = 0; i < this.original.length; ++i) {
                let elementcpid = getChildPath(this.original[i]);
                if (shouldBeSeen(currentcpid, elementcpid))
                    leftOfCut.push(this.original[i]);
                else
                    break;
            }
            this.underlying = leftOfCut;
            for (let i = 0; i < this.underlying.length; ++i) {
                this[i] = this.underlying[i];
            }
        }
        else {
            this.underlying = [];
            for (let i = 0; i < this.original.length; ++i) {
                this.underlying.push(this.original[i]);
                this[i] = this.original[i];
            }
        }
    }

    item(index: number): (T | null) {
        if (document.currentScript == null)
            return this.original[index];
        else
            return this[index] || null;
    }

    get length(): number {
        if (document.currentScript == null)
            return this.original.length;
        else
            return this.underlying.length;
    }

    forEach(callback: Function, thisArg?: NodeListOf<T>): void {
        let thisNodeList: NodeListOf<T> = thisArg;
        if (thisArg == undefined)
            thisNodeList = this;
        for (let i = 0; i < this.underlying.length; ++i) {
            callback.call(this.underlying[i], i, thisNodeList);
        }
    }

    // TODO: keys(), values() and entries()
}

/*
//_embeds()
Object.defineProperty(document, '_embeds', {
    value: function(): MyHTMLCollectionOf<HTMLEmbedElement> {
        let allEmbeds: HTMLCollectionOf<HTMLEmbedElement> = document.embeds;
        let result = new MyHTMLCollectionOf(allEmbeds);
        console.log('inside _embeds: #dom.embeds=', allEmbeds.length);
        return result;
    },
    writable: false
});
//_forms()
Object.defineProperty(document, '_forms', {
    value: function(): MyHTMLCollectionOf<HTMLFormElement> {
        let allForms: HTMLCollectionOf<HTMLFormElement> = document.forms;
        let result = new MyHTMLCollectionOf(allForms);
        console.log('inside _forms: #dom.forms=', allForms.length);
        return result;
    },
    writable: false
});
//_images()
Object.defineProperty(document, '_images', {
    value: function(): MyHTMLCollectionOf<HTMLImageElement> {
        let allImgs: HTMLCollectionOf<HTMLImageElement> = document.images;
        let result = new MyHTMLCollectionOf(allImgs);
        console.log('inside _images: #dom.images=', allImgs.length);
        return result;
    },
    writable: false
});
//_links()
Object.defineProperty(document, '_links', {
    value: function(): MyHTMLCollectionOf<HTMLAnchorElement | HTMLAreaElement> {
        //returns a collection of all <area> elements and <a> elements
        let allLinks: HTMLCollectionOf<HTMLAnchorElement | HTMLAreaElement> =
            document.links;
        let result = new MyHTMLCollectionOf(allLinks);
        console.log('inside _links: #dom.links=', allLinks.length);
        return result;
    },
    writable: false
});
//_plugins
Object.defineProperty(document, '_plugins', {
    value: function(): (MyHTMLCollectionOf<HTMLEmbedElement> | null) {
        //returns null if there are no embeds in the document.
        let allPlugins: (HTMLCollectionOf<HTMLEmbedElement> | null) =
            document.plugins;
        if (allPlugins == null)
            return null;
        else {
            let result = new MyHTMLCollectionOf(allPlugins);
            console.log('inside _plugins: #dom.plugins=', allPlugins.length);
            return result;
        }
    },
    writable: false
});
//_scripts()
Object.defineProperty(document, '_scripts', {
    value: function(): MyHTMLCollectionOf<HTMLScriptElement> {
        let allScripts: HTMLCollectionOf<HTMLScriptElement> =
            document.scripts;
        let result = new MyHTMLCollectionOf(allScripts);
        console.log('inside _script: #dom.scripts=', allScripts.length);
        return result;
    },
    writable: false
});
//styleSheetSets not supported for now.
*/

// TODO: ParentNode -> append() and prepend()

let _getElementsByTagName = document.getElementsByTagName;
document.getElementsByTagName =
    function(name: string): HTMLCollectionOf<Element> {
        let elements: HTMLCollectionOf<Element>;
        elements = _getElementsByTagName.call(document, name);
        return new MyHTMLCollectionOf(elements); //as HTMLCollectionOf<Element>
    };

let _getElementsByClassName = document.getElementsByClassName;
document.getElementsByClassName =
    function(classNames: string): HTMLCollectionOf<Element> {
        let elements = _getElementsByClassName.call(document, classNames);
        return new MyHTMLCollectionOf(elements);
    };

let _getElementById = document.getElementById;
document.getElementById = function(requestedId: string): HTMLElement {
    // returns null if no matching element was found in the document.
    let retVal: HTMLElement = _getElementById.call(document, requestedId);
    if (retVal && document.currentScript) {
        let currentScriptId = getChildPath(document.currentScript);
        if (!shouldBeSeen(currentScriptId, getChildPath(retVal))) {
            // console.log('cut point is ' + currentScriptId);
            // console.log('getElementById returns a node which should not be seen: ' + getChildPath(retVal));
            return null;
        }
    }
    return retVal;
};

let _querySelector = document.querySelector;
document.querySelector = function(selectors: string): Element {
    let element: Element = _querySelector.call(this, selectors);
    if (element && document.currentScript) {
        let currentScriptId = getChildPath(document.currentScript);
        if (!shouldBeSeen(currentScriptId, getChildPath(element))) {
            // console.log('[document.querySelector] accessed an ahead element!');
            return null;
        }
    }
    return element;
}

let _querySelectorAll = document.querySelectorAll;
document.querySelectorAll = function <T extends Element>(selectors: string): NodeListOf<T> {
    //returns the first descendant element of (this) which matches the selectors.
    let elementList: NodeListOf<T> = _element_querySelectorAll.call(this, selectors);
    return new MyNodeListOf(elementList);
};

let _write = document.write;
document.write = function(...text: string[]): void {
    if (document.currentScript) {
        let currentParent: Node = document.currentScript.parentNode;
        let parentChildPath: number[] = getChildPath(currentParent);
        let beforeChildrenLen: number = currentParent.childNodes.length;
        _write.call(this, ...text);
        let numOfAppends = currentParent.childNodes.length - beforeChildrenLen;
        scriptUpdates.push({
            shift: numOfAppends,
            cpid: parentChildPath,
            index: beforeChildrenLen // assuming the text was appended starting from this index
        } as NativeUpdate);
    }
    else {
        _write.call(this, ...text);
        console.log('[write] called on [Document] but not handled!');
    }
};

let _writeln = document.writeln;
document.writeln = function(...text: string[]): void {
    if (document.currentScript) {
        let currentParent: Node = document.currentScript.parentNode;
        let parentChildPath: number[] = getChildPath(currentParent);
        let beforeChildrenLen: number = currentParent.childNodes.length;
        _writeln.call(this, ...text);
        let numOfAppends = currentParent.childNodes.length - beforeChildrenLen;
        scriptUpdates.push({
            shift: numOfAppends,
            cpid: parentChildPath,
            index: beforeChildrenLen // assuming the text was appended starting from this index
        } as NativeUpdate);
    }
    else {
        _writeln.call(this, ...text);
        console.log('[writeln] called on [Document] but not handled!');
    }
};
//----------------------------------------------------------------------------------------------------//
// Element.closest() does not need handling as it should not get affected.
// Element.attachShadow() does not seem require handling
// Element.animate() does not seem require handling.

let _element_getElementsByClassName = Element.prototype.getElementsByClassName;
Element.prototype.getElementsByClassName = function(names: string): HTMLCollectionOf<Element> {
    let elements = _element_getElementsByClassName.call(this, names);
    return new MyHTMLCollectionOf(elements);
}

let _element_getElementsByTagName = Element.prototype.getElementsByTagName;
Element.prototype.getElementsByTagName = function(name: string): HTMLCollectionOf<Element> {
    let elements = _element_getElementsByTagName.call(this, name);
    return new MyHTMLCollectionOf(elements);
};

let _element_getElementsByTagNameNS = Element.prototype.getElementsByTagNameNS;
Element.prototype.getElementsByTagNameNS =
    function <T extends Element>(namespaceURI: string, localName: string): HTMLCollectionOf<T> {
        let elements = _element_getElementsByTagNameNS.call(this, namespaceURI, localName);
        return new MyHTMLCollectionOf(elements);
    };

let _insertAdjacentElement = Element.prototype.insertAdjacentElement;
Element.prototype.insertAdjacentElement = function(position: InsertPosition,
    insertedElement: Element): Element {
    /*
      'beforebegin': Before the targetElement(this) itself.
      'afterbegin': Just inside the targetElement, before its first child.
      'beforeend': Just inside the targetElement, after its last child.
      'afterend': After the targetElement itself.
    */
    let inserted: (Element | null) = _insertAdjacentElement.call(this, position, insertedElement);
    if (inserted != null) { // if native call did not fail
        scriptUpdates.push({
            shift: 1,
            cpid: getChildPath(inserted.parentNode),
            index: getIndexOf(inserted)
        } as NativeUpdate);
    }
    return inserted;
};

let _insertAdjacentHTML = Element.prototype.insertAdjacentHTML;
Element.prototype.insertAdjacentHTML = function(position: InsertPosition,
    text: string): void {
    _insertAdjacentHTML.call(this, position, text);
    console.log('[insertAdjacentHTML] called on [Element] but not handled!');
};

let _insertAdjacentText = Element.prototype.insertAdjacentText;
Element.prototype.insertAdjacentText = function(position: InsertPosition,
    text: string): void {
    _insertAdjacentText.call(this, position, text);
    console.log('[insertAdjacentText] called on [Element] but not handled!');
};

let _element_querySelector = Element.prototype.querySelector;
Element.prototype.querySelector = function(selectors: string): Element {
    //returns the first descendant element of (this) which matches the selectors.
    let element: Element = _element_querySelector.call(this, selectors);
    if (element && document.currentScript) {
        let currentScriptId = getChildPath(document.currentScript);
        if (!shouldBeSeen(currentScriptId, getChildPath(element))) {
            return null;
        }
    }
    return element;
};

let _element_querySelectorAll = Element.prototype.querySelectorAll;
Element.prototype.querySelectorAll = function <T extends Element>(selectors: string): NodeListOf<T> {
    //returns the first descendant element of (this) which matches the selectors.
    let elementList: NodeListOf<T> = _element_querySelectorAll.call(this, selectors);
    return new MyNodeListOf(elementList);
};

//----------------------------------------------------------------------------------------------------//
let _insertBefore = Node.prototype.insertBefore;
Node.prototype.insertBefore =
    function <T extends Node>(newChild: T, refChild: Node): T {
        let reference: Node | null = null;
        if (refChild != undefined)
            reference = refChild;
        let parentChildPath: number[] = getChildPath(this);
        let insertedNode: T = _insertBefore.call(this, newChild, reference);
        let targetIndex: number = getIndexOf(insertedNode);

        scriptUpdates.push({
            shift: 1,
            cpid: parentChildPath,
            index: targetIndex
        } as NativeUpdate);
        return insertedNode;
    };

let _appendChild = Node.prototype.appendChild;
Node.prototype.appendChild =
    function <T extends Node>(newChild: T): T {
        let parentChildPath: number[] = getChildPath(this);
        // Note: If newchild already exists in the DOM, it is first removed.
        let previousParent: (Node | null) = newChild.parentNode;
        if (previousParent) {
            let removedIndex: number = getIndexOf(newChild); // in parent.childNodes
            // if newchild already exists in DOM, then its parent is affected.
            scriptUpdates.push({
                shift: -1,
                cpid: getChildPath(previousParent),
                index: removedIndex
            } as NativeUpdate);
        }

        let appendedChild: T = _appendChild.call(this, newChild);

        if (parentChildPath.length != 0) { //!= newly created node, not yet in DOM
            scriptUpdates.push({
                shift: 1,
                cpid: parentChildPath,
                index: getIndexOf(appendedChild)
            } as NativeUpdate);
        }
        return appendedChild;
    };

let _replaceChild = Node.prototype.replaceChild;
Node.prototype.replaceChild =
    function <T extends Node>(newChild: Node, oldChild: T): T {
        // Note: If newchild already exists in the DOM, it is first removed.
        // (this) is the parentNode. Returns the replaced node (oldchild).
        let previousParent: (Node | null) = newChild.parentNode;
        if (previousParent) {
            let removedIndex: number = getIndexOf(newChild); // in parent.childNodes
            // if newchild already exists in DOM, then its parent is affected.
            scriptUpdates.push({
                shift: -1,
                cpid: getChildPath(previousParent),
                index: removedIndex
            } as NativeUpdate);
        }

        let replacedNode: T = _replaceChild.call(this, newChild, oldChild);
        return replacedNode;
    };

let _removeChild = Node.prototype.removeChild;
Node.prototype.removeChild = function <T extends Node>(oldChild: T): T {
    let parentChildPath: number[] = getChildPath(this);
    let removeTargetIndex: number = getIndexOf(oldChild);

    let removed: T = _removeChild.call(this, oldChild);

    scriptUpdates.push({
        shift: -1,
        cpid: parentChildPath,
        index: removeTargetIndex
    } as NativeUpdate);
    return removed;
};


function updateNativeInserts(nativeUpdate: NativeUpdate): void {
    // update the existing nativeInserts based on these new nativeUpdate
    // meanwhile throw away those which are now behind now firstUnseen update.
    let i = 0;
    while (i < nativeInserts.length) {
        if (comparecpidPositions(lastSeencpid, nativeInserts[i]) < 0) {
            nativeInserts.splice(i, 1); // throw away i-th index
        }
        else {
            updateAffectedAncestors(nativeInserts[i], nativeUpdate);
            ++i;
        }
    }
    // then add these new scriptUpdates to the nativeInserts.
    if (nativeUpdate.shift == 1) { // only for native Inserts
        let insertedNodecpid: number[] = nativeUpdate.cpid.slice(); //copy cpid
        insertedNodecpid.push(nativeUpdate.index);
        if (comparecpidPositions(lastSeencpid, insertedNodecpid) > 0) {
            // this scriptUpdates should be kept so that we can make an exception for them
            // and let them be seen by native method calls.
            nativeInserts.push(insertedNodecpid);
        }
    }
}

function updateAffectedAncestors(jsoncpid: number[], nativeUpdate: NativeUpdate): boolean {
    //jsoncpid is passed by reference -> returns true if jsoncpid was updated.
    // checks if native update affected any one of jsonUpdate ancestors
    // which causes a shift to the position of jsonUpdate cpid.
    if (isStrictPrefix(nativeUpdate.cpid, jsoncpid)) {
        // the level of tree where this shift happened is nativeUpdate.cpid.length
        let affectedLevel: number = nativeUpdate.cpid.length;
        if (nativeUpdate.index <= jsoncpid[affectedLevel]) {
            jsoncpid[affectedLevel] += nativeUpdate.shift;
            return true;
        }
        // else -> native scripts are allowed to affect node which are ahead of this point.
        //    throw "[Error] Native script affected nodes ahead of time!"
    }
    return false;
}

function updateJSONcpids(): void {
    // Solves interleaving Problem (Problem I):
    // JSON cpids affected by the native script updates.
    // jsonUpdates are empty => probably XHR response is not yet received
    if (jsonUpdates.length == 0)
        return;

    for (let i = 0; i < scriptUpdates.length; ++i) {
        for (let j = 0; j < jsonUpdates.length; ++j) {
            // updates the main cpid of Delete/Insert/Merge/Move if needed.
            let affected: boolean = updateAffectedAncestors(jsonUpdates[j].cpid,
                scriptUpdates[i]);
            if (!affected) {
                // TODO: this could be more optimized -> less looping on cpids
                if (isEqualcpid(jsonUpdates[j].cpid, scriptUpdates[i].cpid)) {
                    // Insert update: check if native script has inserted/deleted node
                    // to/from parent node (== jsonUpdate.cpid) and therefore shifted i
                    if (jsonUpdates[j].i != undefined) {
                        jsonUpdates[j].i += scriptUpdates[i].shift
                        affected = true;
                    }
                    // else
                    //    throw '[Error] Native script affected current node ahead of time!';
                }

            }
            // Assuming jsonUpdate is Insert or Move, reassigning affected should be ok
            // Move update: updates the new parent cpid (np) if needed.
            if (jsonUpdates[j].np != null) { //Move
                affected = updateAffectedAncestors(jsonUpdates[j].np, scriptUpdates[i]);
            }
        }

        updateNativeInserts(scriptUpdates[i]);
    }
    scriptUpdates = [];
}

function createElementFromEdit(edit: Edit): Element {
    let newElement: Element = document.createElement(edit.n);
    setElementAttributes(newElement, edit.attrs);

    // if this update has a 'c' attribute -> it could be an array of children or content string
    // in case of former, each element of array is a JSON update representing an Element type of Node
    // which can have its own 'c' property.
    if (edit.hasOwnProperty('c'))
        addChildren(newElement, edit.c);

    return newElement;
}

function setElementAttributes(element: Element, attrs: object): void {
    for (let key in attrs) {
        let strValue = attrs[key]
        if (Array.isArray(attrs[key])) // attribute value is a list of strings
            strValue = attrs[key].join(' ');

        if (element.hasAttribute(key)) {
            if (strValue == null) // remove attribute if they value is null.
                element.removeAttribute(key);
            else {
                let attrNode: Attr = element.getAttributeNode(key);
                attrNode.value = strValue;
                // if (strValue !== element.getAttribute(key)) {
                // console.log('[Warning] Setting attr', key, ' to ', strValue);
                // }
            }
        } else {
            if (!key.includes(']') && !key.includes('['))
                element.setAttribute(key, strValue);
        }
    }
}

function addChildren(parent: Node, innerUpdate: (Edit[] | string)): void {
    if (Array.isArray(innerUpdate)) { // array of json objects
        while (innerUpdate.length > 0) {
            //important to call the native _appendChild method;
            _appendChild.call(parent, createElementFromEdit(innerUpdate[0]));
            innerUpdate.shift();
        }
    } else { // it should be string
        let newChild: Text = document.createTextNode(innerUpdate);
        _appendChild.call(parent, newChild);
    }
}

function applyJsonUpdates(): void {
    // This function applies as much of edits as it can on the current DOM,
    // it also takes the applied edits out of the global list (jsonUpdates).
    // Each JSON object is corresponding to an EDIT in python code.

    let pauseApplying: boolean = false;
    while (jsonUpdates.length > 0 && !pauseApplying) {
        let edit: Edit = jsonUpdates[0];
        if (scriptUpdates.length > 0) {
            updateJSONcpids();
        }
        try {
            let selected: (Node | null) = findNodeBycpid(edit.cpid);
            if (selected == null)
                throw 'Could not apply edit; Node [' + edit.cpid + '] not found!';
            else
                lastSeencpid = edit.cpid;

            if (edit.hasOwnProperty('_type')) { // Delete
                selected.parentNode.removeChild(selected);
            }
            else if (edit.hasOwnProperty('i')) { // Insert
                let referenceChild: (Node | null) = null;
                // i = the target index where this new node is inserted at
                if (edit.i < selected.childNodes.length)
                    referenceChild = selected.childNodes[edit.i];
                else if (edit.i > selected.childNodes.length)
                    throw 'Could not apply insert; target_index out of bound!';

                // n = tag name to be inserted,
                // c = either the content or children based on the node type.
                let newNode: (Element | Text);
                if (edit.hasOwnProperty('n'))
                    newNode = createElementFromEdit(edit);
                else // TextContent
                    newNode = document.createTextNode(edit.c as string);

                // selected.insertBefore(newNode, referenceChild);
                _insertBefore.call(selected, newNode, referenceChild);

            }
            else if (edit.hasOwnProperty('np')) { // Move
                // Move selected node and append it to the the new parent node
                let newParent: Node = findNodeBycpid(edit.np);
                if (newParent == null)
                    throw 'Could not apply move; Parent node [' + edit.np + '] not found!';

                // newParent.appendChild(selected);
                _appendChild.call(newParent, selected);
            }
            else { //Merge
                setElementAttributes((selected as Element), edit.attrs);
            }
            jsonUpdates.shift();
        } catch (err) {
            // console.log('Ignore the following error if applyUpdatesCalled is false ->', applyUpdatesCalled);
            // console.log(err);
            // console.log('edit=', edit);
            pauseApplying = true;
        }
    }

    if (applyUpdatesCalled && !jsonUpdates.length) {
        // console.log('YESSSS! WE ARE DONE!\\:D/');
        document.getElementById = _getElementById;
        document.getElementsByClassName = _getElementsByTagName;
        document.getElementsByTagName = _getElementsByTagName;
        document.querySelector = _querySelector;
        document.querySelectorAll = _querySelectorAll;
        document.write = _write;
        document.writeln = _writeln;
        Element.prototype.getElementsByClassName = _element_getElementsByClassName;
        Element.prototype.getElementsByTagName = _element_getElementsByTagName;
        Element.prototype.getElementsByTagNameNS = _element_getElementsByTagNameNS;
        Element.prototype.insertAdjacentElement = _insertAdjacentElement;
        Element.prototype.insertAdjacentHTML = _insertAdjacentHTML;
        Element.prototype.querySelector = _element_querySelector;
        Element.prototype.querySelectorAll = _element_querySelectorAll;
    }

    applyUpdatesCalled = true;

}

//-----------------------Main part of JS-------------------------------
let updateXHR: XMLHttpRequest = new XMLHttpRequest();
// updateXHR.addEventListener("load", update_callback);
updateXHR.onload = function(): void {
    // console.log('Got back the update');
    jsonUpdates = updateXHR.response.edits;
    applyJsonUpdates();
};
updateXHR.open('GET', 'update.json', true);
updateXHR.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
updateXHR.responseType = 'json'; // parses the response == JSON.parse(req.responseText);
updateXHR.send(null);
let patcher: HTMLElement = document.getElementById('main-patcher');
patcher.remove();
//---------------------------------------------------------------------
