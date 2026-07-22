// Adds mouse-wheel paging to a v-data-table.
//
// Usage in a component:
//   import WheelPagingMixin from '../mixins/WheelPagingMixin.js'
//   mixins: [WheelPagingMixin]
//
// and on the <v-data-table>:
//   :page.sync="page"
//   @page-count="pageCount = $event"
//   @wheel.native.prevent="onWheelPage"
//
// Scrolling the wheel down moves to the next page, up moves to the
// previous page. Paging stops at the first and last page.
//
// The current page is remembered per panel for the lifetime of the
// session (survives closing and reopening the cheat UI, which destroys
// the panels). Components rendered more than once (e.g. the item/weapon/
// armor tabs share the ItemTableTab component) can pass a distinct
// `page-store-key` prop to keep independent page memory.
const pageStore = {}

export default {
    props: {
        pageStoreKey: {
            type: String,
            default: null
        }
    },

    data () {
        return {
            page: 1,
            pageCount: 1
        }
    },

    created () {
        // non-reactive throttle timestamp (avoids triggering re-renders)
        this._lastWheelPageTime = 0

        // restore the page from the previous time this panel was open
        this._pageStoreKey = this.pageStoreKey || this.$options.name
        const savedPage = pageStore[this._pageStoreKey]
        if (savedPage) {
            this.page = savedPage
        }
    },

    watch: {
        page (value) {
            pageStore[this._pageStoreKey] = value
        }
    },

    methods: {
        onWheelPage (event) {
            if (!event || !event.deltaY) {
                return
            }

            // throttle rapid wheel events (e.g. trackpads) so a single
            // gesture does not skip multiple pages at once
            const now = Date.now()
            if (now - this._lastWheelPageTime < 120) {
                return
            }
            this._lastWheelPageTime = now

            if (event.deltaY > 0) {
                if (this.page < this.pageCount) {
                    this.page += 1
                }
            } else if (event.deltaY < 0) {
                if (this.page > 1) {
                    this.page -= 1
                }
            }
        }
    }
}
