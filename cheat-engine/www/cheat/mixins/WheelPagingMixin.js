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
export default {
    data () {
        return {
            page: 1,
            pageCount: 1
        }
    },

    created () {
        // non-reactive throttle timestamp (avoids triggering re-renders)
        this._lastWheelPageTime = 0
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
